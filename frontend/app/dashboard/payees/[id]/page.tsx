"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { payeesAPI, categoriesAPI } from "@/lib/api";
import { Payee, PayeeUpdate, Category, PayeeTransaction, PayeeStats } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";

export default function EditPayeePage() {
  const router = useRouter();
  const params = useParams();
  const payeeId = parseInt(params.id as string);
  const { isAuthenticated, loading: authLoading } = useAuth();

  const [payee, setPayee] = useState<Payee | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [transactions, setTransactions] = useState<PayeeTransaction[]>([]);
  const [stats, setStats] = useState<PayeeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

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
      const [payeeData, categoriesData, transactionsData, statsData] = await Promise.all([
        payeesAPI.getById(payeeId),
        categoriesAPI.getAll(),
        payeesAPI.getTransactions(payeeId, 25),
        payeesAPI.getStats(payeeId),
      ]);

      setPayee(payeeData);
      setCategories(categoriesData);
      setTransactions(transactionsData);
      setStats(statsData);

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
