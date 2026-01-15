"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { rulesAPI, categoriesAPI } from "@/lib/api";
import {
  CategorizationRuleCreate,
  Category,
  MatchType,
  TransactionTypeFilter,
} from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";

export default function NewRulePage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState<CategorizationRuleCreate>({
    name: "",
    priority: 100,
    enabled: true,
    payee_pattern: "",
    payee_match_type: MatchType.CONTAINS,
    description_pattern: "",
    description_match_type: MatchType.CONTAINS,
    amount_min: "",
    amount_max: "",
    transaction_type: undefined,
    category_id: undefined,
    new_payee: "",
    notes_append: "",
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadCategories();
    }
  }, [isAuthenticated]);

  const loadCategories = async () => {
    try {
      const data = await categoriesAPI.getAll();
      setCategories(data);
    } catch (err: any) {
      console.error("Failed to load categories", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      setError("Rule name is required");
      return;
    }

    if (!formData.payee_pattern && !formData.description_pattern) {
      setError("At least one condition (payee or description) is required");
      return;
    }

    try {
      setLoading(true);
      setError("");

      // Clean up empty strings
      const cleanedData = {
        ...formData,
        payee_pattern: formData.payee_pattern || undefined,
        payee_match_type: formData.payee_pattern ? formData.payee_match_type : undefined,
        description_pattern: formData.description_pattern || undefined,
        description_match_type: formData.description_pattern ? formData.description_match_type : undefined,
        amount_min: formData.amount_min || undefined,
        amount_max: formData.amount_max || undefined,
        new_payee: formData.new_payee || undefined,
        notes_append: formData.notes_append || undefined,
      };

      await rulesAPI.create(cleanedData);
      router.push("/dashboard/rules");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create rule");
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="md:flex md:items-center md:justify-between">
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                Create Categorization Rule
              </h1>
            </div>
          </div>

          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-6 bg-white shadow sm:rounded-lg p-6">
            {/* Basic Settings */}
            <div>
              <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Basic Settings</h3>

              <div className="grid grid-cols-1 gap-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Rule Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="priority" className="block text-sm font-medium text-gray-700">
                      Priority
                    </label>
                    <input
                      type="number"
                      id="priority"
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                    <p className="mt-1 text-xs text-gray-500">Higher priority rules run first</p>
                  </div>

                  <div className="flex items-center pt-6">
                    <input
                      type="checkbox"
                      id="enabled"
                      checked={formData.enabled}
                      onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="enabled" className="ml-2 block text-sm text-gray-900">
                      Enable rule immediately
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Conditions */}
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Conditions</h3>
              <p className="text-sm text-gray-500 mb-4">Define when this rule should match a transaction</p>

              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-2">
                    <label htmlFor="payee_pattern" className="block text-sm font-medium text-gray-700">
                      Payee Pattern
                    </label>
                    <input
                      type="text"
                      id="payee_pattern"
                      value={formData.payee_pattern}
                      onChange={(e) => setFormData({ ...formData, payee_pattern: e.target.value })}
                      placeholder="e.g., AMAZON, STARBUCKS"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="payee_match_type" className="block text-sm font-medium text-gray-700">
                      Match Type
                    </label>
                    <select
                      id="payee_match_type"
                      value={formData.payee_match_type}
                      onChange={(e) => setFormData({ ...formData, payee_match_type: e.target.value as MatchType })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value={MatchType.CONTAINS}>Contains</option>
                      <option value={MatchType.STARTS_WITH}>Starts with</option>
                      <option value={MatchType.ENDS_WITH}>Ends with</option>
                      <option value={MatchType.EXACT}>Exact match</option>
                      <option value={MatchType.REGEX}>Regex</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-2">
                    <label htmlFor="description_pattern" className="block text-sm font-medium text-gray-700">
                      Description Pattern
                    </label>
                    <input
                      type="text"
                      id="description_pattern"
                      value={formData.description_pattern}
                      onChange={(e) => setFormData({ ...formData, description_pattern: e.target.value })}
                      placeholder="e.g., groceries, gas"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="description_match_type" className="block text-sm font-medium text-gray-700">
                      Match Type
                    </label>
                    <select
                      id="description_match_type"
                      value={formData.description_match_type}
                      onChange={(e) => setFormData({ ...formData, description_match_type: e.target.value as MatchType })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value={MatchType.CONTAINS}>Contains</option>
                      <option value={MatchType.STARTS_WITH}>Starts with</option>
                      <option value={MatchType.ENDS_WITH}>Ends with</option>
                      <option value={MatchType.EXACT}>Exact match</option>
                      <option value={MatchType.REGEX}>Regex</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="amount_min" className="block text-sm font-medium text-gray-700">
                      Minimum Amount
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      id="amount_min"
                      value={formData.amount_min}
                      onChange={(e) => setFormData({ ...formData, amount_min: e.target.value })}
                      placeholder="0.00"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="amount_max" className="block text-sm font-medium text-gray-700">
                      Maximum Amount
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      id="amount_max"
                      value={formData.amount_max}
                      onChange={(e) => setFormData({ ...formData, amount_max: e.target.value })}
                      placeholder="0.00"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="transaction_type" className="block text-sm font-medium text-gray-700">
                    Transaction Type
                  </label>
                  <select
                    id="transaction_type"
                    value={formData.transaction_type || ""}
                    onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value as TransactionTypeFilter || undefined })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    <option value="">Any</option>
                    <option value={TransactionTypeFilter.DEBIT}>Debit</option>
                    <option value={TransactionTypeFilter.CREDIT}>Credit</option>
                    <option value={TransactionTypeFilter.TRANSFER}>Transfer</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Actions</h3>
              <p className="text-sm text-gray-500 mb-4">What should happen when this rule matches?</p>

              <div className="space-y-4">
                <div>
                  <label htmlFor="category_id" className="block text-sm font-medium text-gray-700">
                    Assign Category
                  </label>
                  <select
                    id="category_id"
                    value={formData.category_id || ""}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value ? parseInt(e.target.value) : undefined })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    <option value="">None</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="new_payee" className="block text-sm font-medium text-gray-700">
                    Rename Payee To
                  </label>
                  <input
                    type="text"
                    id="new_payee"
                    value={formData.new_payee}
                    onChange={(e) => setFormData({ ...formData, new_payee: e.target.value })}
                    placeholder="e.g., Amazon"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label htmlFor="notes_append" className="block text-sm font-medium text-gray-700">
                    Append to Notes
                  </label>
                  <textarea
                    id="notes_append"
                    rows={3}
                    value={formData.notes_append}
                    onChange={(e) => setFormData({ ...formData, notes_append: e.target.value })}
                    placeholder="Add notes to matching transactions"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={() => router.push("/dashboard/rules")}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? "Creating..." : "Create Rule"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}
