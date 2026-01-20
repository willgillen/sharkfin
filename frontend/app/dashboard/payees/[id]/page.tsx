"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { payeesAPI, categoriesAPI } from "@/lib/api";
import {
  Payee,
  PayeeUpdate,
  Category,
  PayeeTransaction,
  PayeeStats,
  PayeePattern,
  PayeePatternCreate,
  PatternType,
} from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";

const PATTERN_TYPE_LABELS: Record<PatternType, string> = {
  description_contains: "Contains",
  exact_match: "Exact Match",
  fuzzy_match_base: "Fuzzy Match",
  description_regex: "Regex",
};

const PATTERN_TYPE_DESCRIPTIONS: Record<PatternType, string> = {
  description_contains: "Matches if the pattern text appears anywhere in the transaction description (case-insensitive)",
  exact_match: "Matches if the extracted payee name exactly matches the pattern",
  fuzzy_match_base: "Matches if the extracted name is at least 80% similar to the pattern",
  description_regex: "Advanced: matches using a regular expression pattern",
};

export default function EditPayeePage() {
  const router = useRouter();
  const params = useParams();
  const payeeId = parseInt(params.id as string);
  const { isAuthenticated, loading: authLoading } = useAuth();

  const [payee, setPayee] = useState<Payee | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [transactions, setTransactions] = useState<PayeeTransaction[]>([]);
  const [stats, setStats] = useState<PayeeStats | null>(null);
  const [patterns, setPatterns] = useState<PayeePattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Pattern form state
  const [showAddPattern, setShowAddPattern] = useState(false);
  const [newPattern, setNewPattern] = useState<PayeePatternCreate>({
    pattern_type: "description_contains",
    pattern_value: "",
    confidence_score: "0.80",
  });
  const [patternError, setPatternError] = useState("");
  const [savingPattern, setSavingPattern] = useState(false);

  // Test pattern state
  const [testDescription, setTestDescription] = useState("");
  const [testResult, setTestResult] = useState<{ matches: boolean; details: string } | null>(null);
  const [testing, setTesting] = useState(false);

  const [formData, setFormData] = useState<PayeeUpdate>({
    canonical_name: "",
    default_category_id: undefined,
    payee_type: "",
    logo_url: "",
    notes: "",
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated, payeeId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [payeeData, categoriesData, transactionsData, statsData, patternsData] = await Promise.all([
        payeesAPI.getById(payeeId),
        categoriesAPI.getAll(),
        payeesAPI.getTransactions(payeeId, 25),
        payeesAPI.getStats(payeeId),
        payeesAPI.getPatterns(payeeId),
      ]);

      setPayee(payeeData);
      setCategories(categoriesData);
      setTransactions(transactionsData);
      setStats(statsData);
      setPatterns(patternsData);

      // Populate form with existing data
      setFormData({
        canonical_name: payeeData.canonical_name,
        default_category_id: payeeData.default_category_id || undefined,
        payee_type: payeeData.payee_type || "",
        logo_url: payeeData.logo_url || "",
        notes: payeeData.notes || "",
      });

      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load payee");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");

    try {
      // Only send fields that have values
      const updateData: PayeeUpdate = {};
      if (formData.canonical_name) updateData.canonical_name = formData.canonical_name;
      if (formData.default_category_id) updateData.default_category_id = formData.default_category_id;
      if (formData.payee_type) updateData.payee_type = formData.payee_type;
      if (formData.logo_url) updateData.logo_url = formData.logo_url;
      if (formData.notes) updateData.notes = formData.notes;

      await payeesAPI.update(payeeId, updateData);
      router.push("/dashboard/payees");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update payee");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    router.push("/dashboard/payees");
  };

  const handleAddPattern = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPattern(true);
    setPatternError("");

    try {
      const pattern = await payeesAPI.createPattern(payeeId, newPattern);
      setPatterns([pattern, ...patterns]);
      setShowAddPattern(false);
      setNewPattern({
        pattern_type: "description_contains",
        pattern_value: "",
        confidence_score: "0.80",
      });
      setTestResult(null);
      setTestDescription("");
    } catch (err: any) {
      setPatternError(err.response?.data?.detail || "Failed to create pattern");
    } finally {
      setSavingPattern(false);
    }
  };

  const handleDeletePattern = async (patternId: number) => {
    if (!confirm("Are you sure you want to delete this pattern? This may affect future transaction matching.")) {
      return;
    }

    try {
      await payeesAPI.deletePattern(patternId);
      setPatterns(patterns.filter((p) => p.id !== patternId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete pattern");
    }
  };

  const handleTestPattern = async () => {
    if (!testDescription.trim() || !newPattern.pattern_value.trim()) {
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const result = await payeesAPI.testPattern(
        newPattern.pattern_type,
        newPattern.pattern_value,
        testDescription
      );
      setTestResult({
        matches: result.matches,
        details: result.match_details || "",
      });
    } catch (err: any) {
      setTestResult({
        matches: false,
        details: err.response?.data?.detail || "Test failed",
      });
    } finally {
      setTesting(false);
    }
  };

  const formatCurrency = (amount: string | number) => {
    const num = typeof amount === "string" ? parseFloat(amount) : amount;
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(num);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getSourceBadge = (source: string) => {
    switch (source) {
      case "import_learning":
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">
            Learned
          </span>
        );
      case "user_created":
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-800">
            Manual
          </span>
        );
      case "known_merchant":
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-purple-100 text-purple-800">
            Known
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-800">
            {source}
          </span>
        );
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (!payee) {
    return (
      <DashboardLayout>
        <div className="px-4 sm:px-0">
          <div className="text-center py-12">
            <p className="text-red-600">Payee not found</p>
            <button
              onClick={() => router.push("/dashboard/payees")}
              className="mt-4 text-blue-600 hover:text-blue-800"
            >
              Back to Payees
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Edit Payee</h1>
          <p className="mt-2 text-sm text-gray-600">
            Update payee information and default settings
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form Column */}
          <div className="lg:col-span-2">
            <div className="bg-white shadow rounded-lg p-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Canonical Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Payee Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.canonical_name}
                    onChange={(e) => setFormData({ ...formData, canonical_name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    required
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    The canonical (normalized) name for this payee
                  </p>
                </div>

                {/* Default Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Category
                  </label>
                  <select
                    value={formData.default_category_id || ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        default_category_id: e.target.value ? parseInt(e.target.value) : undefined,
                      })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  >
                    <option value="">None</option>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name} ({category.type})
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    Auto-fill this category when selecting this payee in transactions
                  </p>
                </div>

                {/* Payee Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Payee Type
                  </label>
                  <select
                    value={formData.payee_type || ""}
                    onChange={(e) => setFormData({ ...formData, payee_type: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  >
                    <option value="">Select type...</option>
                    <option value="grocery">Grocery</option>
                    <option value="restaurant">Restaurant</option>
                    <option value="gas">Gas Station</option>
                    <option value="utility">Utility</option>
                    <option value="online_retail">Online Retail</option>
                    <option value="entertainment">Entertainment</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="transportation">Transportation</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                {/* Logo URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Logo URL
                  </label>
                  <input
                    type="url"
                    value={formData.logo_url || ""}
                    onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                    placeholder="https://example.com/logo.png"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    URL to a logo image for this payee
                  </p>
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notes
                  </label>
                  <textarea
                    value={formData.notes || ""}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={3}
                    placeholder="Optional notes about this payee..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={handleCancel}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? "Saving..." : "Save Changes"}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Stats Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Spending Stats Card */}
            {stats && (
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Spending Summary</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Total Spent (All Time)</span>
                    <span className="text-lg font-semibold text-red-600">
                      {formatCurrency(stats.total_spent_all_time)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">This Month</span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(stats.total_spent_this_month)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">This Year</span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(stats.total_spent_this_year)}
                    </span>
                  </div>
                  {parseFloat(stats.total_income_all_time) > 0 && (
                    <div className="flex justify-between items-center border-t pt-4">
                      <span className="text-sm text-gray-600">Total Income</span>
                      <span className="text-lg font-semibold text-green-600">
                        {formatCurrency(stats.total_income_all_time)}
                      </span>
                    </div>
                  )}
                  <div className="border-t pt-4 space-y-2">
                    {stats.average_transaction_amount && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Avg Transaction</span>
                        <span className="font-medium text-gray-900">
                          {formatCurrency(stats.average_transaction_amount)}
                        </span>
                      </div>
                    )}
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Transaction Count</span>
                      <span className="font-medium text-gray-900">{stats.transaction_count}</span>
                    </div>
                    {stats.first_transaction_date && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">First Transaction</span>
                        <span className="text-sm text-gray-900">
                          {formatDate(stats.first_transaction_date)}
                        </span>
                      </div>
                    )}
                    {stats.last_transaction_date && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Last Transaction</span>
                        <span className="text-sm text-gray-900">
                          {formatDate(stats.last_transaction_date)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Payee Info Card */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Payee Info</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Created</span>
                  <span className="text-gray-900">{formatDate(payee.created_at)}</span>
                </div>
                {payee.updated_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Last Updated</span>
                    <span className="text-gray-900">{formatDate(payee.updated_at)}</span>
                  </div>
                )}
                {payee.last_used_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Last Used</span>
                    <span className="text-gray-900">{formatDate(payee.last_used_at)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Matching Patterns Section */}
        <div className="mt-6 bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Matching Patterns</h3>
              <p className="text-sm text-gray-500">
                Patterns used to automatically match transactions to this payee during import
              </p>
            </div>
            <button
              onClick={() => setShowAddPattern(!showAddPattern)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              {showAddPattern ? "Cancel" : "+ Add Pattern"}
            </button>
          </div>

          {/* Add Pattern Form */}
          {showAddPattern && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <form onSubmit={handleAddPattern} className="space-y-4">
                {patternError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-800">{patternError}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Pattern Type
                    </label>
                    <select
                      value={newPattern.pattern_type}
                      onChange={(e) =>
                        setNewPattern({ ...newPattern, pattern_type: e.target.value as PatternType })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 text-sm"
                    >
                      {(Object.keys(PATTERN_TYPE_LABELS) as PatternType[]).map((type) => (
                        <option key={type} value={type}>
                          {PATTERN_TYPE_LABELS[type]}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      {PATTERN_TYPE_DESCRIPTIONS[newPattern.pattern_type as PatternType]}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Pattern Value
                    </label>
                    <input
                      type="text"
                      value={newPattern.pattern_value}
                      onChange={(e) => setNewPattern({ ...newPattern, pattern_value: e.target.value })}
                      placeholder="e.g., UBER, STARBUCKS"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 text-sm"
                      required
                    />
                    {newPattern.pattern_type === "description_contains" && (
                      <p className="mt-1 text-xs text-gray-500">Must be at least 4 characters</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Confidence Score
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.05"
                      value={newPattern.confidence_score}
                      onChange={(e) => setNewPattern({ ...newPattern, confidence_score: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 text-sm"
                    />
                    <p className="mt-1 text-xs text-gray-500">0.85+ = high confidence</p>
                  </div>
                </div>

                {/* Test Pattern Section */}
                <div className="border-t pt-4 mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Test Pattern (Optional)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={testDescription}
                      onChange={(e) => setTestDescription(e.target.value)}
                      placeholder="Enter a sample transaction description to test..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-gray-900 text-sm"
                    />
                    <button
                      type="button"
                      onClick={handleTestPattern}
                      disabled={testing || !testDescription.trim() || !newPattern.pattern_value.trim()}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50"
                    >
                      {testing ? "Testing..." : "Test"}
                    </button>
                  </div>
                  {testResult && (
                    <div
                      className={`mt-2 p-2 rounded-md text-sm ${
                        testResult.matches
                          ? "bg-green-50 text-green-800 border border-green-200"
                          : "bg-yellow-50 text-yellow-800 border border-yellow-200"
                      }`}
                    >
                      <span className="font-medium">
                        {testResult.matches ? "Match!" : "No Match"}
                      </span>
                      {testResult.details && <span className="ml-2">- {testResult.details}</span>}
                    </div>
                  )}
                </div>

                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddPattern(false);
                      setPatternError("");
                      setTestResult(null);
                    }}
                    className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingPattern}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {savingPattern ? "Creating..." : "Create Pattern"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Patterns List */}
          {patterns.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Pattern Value
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Confidence
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Matches
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Source
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {patterns.map((pattern) => (
                    <tr key={pattern.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">
                          {PATTERN_TYPE_LABELS[pattern.pattern_type as PatternType] || pattern.pattern_type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded text-gray-800">
                          {pattern.pattern_value}
                        </code>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={`text-sm font-medium ${
                            parseFloat(pattern.confidence_score) >= 0.85
                              ? "text-green-600"
                              : parseFloat(pattern.confidence_score) >= 0.70
                              ? "text-yellow-600"
                              : "text-gray-600"
                          }`}
                        >
                          {(parseFloat(pattern.confidence_score) * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {pattern.match_count}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {getSourceBadge(pattern.source)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <button
                          onClick={() => handleDeletePattern(pattern.id)}
                          className="text-red-600 hover:text-red-800 text-sm font-medium"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No matching patterns yet.</p>
              <p className="text-sm mt-1">
                Patterns are automatically learned when you import transactions, or you can add them manually.
              </p>
            </div>
          )}
        </div>

        {/* Recent Transactions Section */}
        <div className="mt-6 bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Recent Transactions</h3>
            <span className="text-sm text-gray-500">
              Showing last {transactions.length} transactions
            </span>
          </div>

          {transactions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Account
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((txn) => (
                    <tr
                      key={txn.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => router.push(`/dashboard/transactions?highlight=${txn.id}`)}
                    >
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(txn.date)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                        {txn.description || "-"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {txn.account_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {txn.category_name || "-"}
                      </td>
                      <td
                        className={`px-4 py-3 whitespace-nowrap text-sm text-right font-medium ${
                          txn.type === "debit" ? "text-red-600" : "text-green-600"
                        }`}
                      >
                        {txn.type === "debit" ? "-" : "+"}
                        {formatCurrency(txn.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No transactions found for this payee
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
