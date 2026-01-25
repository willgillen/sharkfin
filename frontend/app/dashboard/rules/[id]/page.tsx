"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { rulesAPI, categoriesAPI } from "@/lib/api";
import {
  CategorizationRule,
  CategorizationRuleUpdate,
  Category,
  MatchType,
  TransactionTypeFilter,
} from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Input, Select, Textarea } from "@/components/ui";

export default function EditRulePage() {
  const router = useRouter();
  const params = useParams();
  const ruleId = parseInt(params.id as string);
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [rule, setRule] = useState<CategorizationRule | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState<CategorizationRuleUpdate>({});

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated && ruleId) {
      loadRule();
      loadCategories();
    }
  }, [isAuthenticated, ruleId]);

  const loadRule = async () => {
    try {
      setLoading(true);
      const data = await rulesAPI.getById(ruleId);
      setRule(data);
      setFormData({
        name: data.name,
        priority: data.priority,
        enabled: data.enabled,
        payee_pattern: data.payee_pattern || "",
        payee_match_type: data.payee_match_type,
        description_pattern: data.description_pattern || "",
        description_match_type: data.description_match_type,
        amount_min: data.amount_min || "",
        amount_max: data.amount_max || "",
        transaction_type: data.transaction_type,
        category_id: data.category_id,
        new_payee: data.new_payee || "",
        notes_append: data.notes_append || "",
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load rule");
    } finally {
      setLoading(false);
    }
  };

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

    if (!formData.name?.trim()) {
      setError("Rule name is required");
      return;
    }

    try {
      setSaving(true);
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

      await rulesAPI.update(ruleId, cleanedData);
      router.push("/dashboard/rules");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update rule");
    } finally {
      setSaving(false);
    }
  };

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-text-secondary">Loading...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (!rule) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <h3 className="text-sm font-medium text-text-primary">Rule not found</h3>
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
              <h1 className="text-2xl font-bold leading-7 text-text-primary sm:text-3xl sm:truncate">
                Edit Rule
              </h1>
              {rule.auto_created && (
                <p className="mt-1 text-sm text-text-secondary">
                  This rule was auto-generated from your transaction patterns
                </p>
              )}
            </div>
          </div>

          {error && (
            <div className="mt-4 bg-danger-50 border border-danger-200 rounded-md p-4">
              <p className="text-sm text-danger-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-6 bg-white shadow sm:rounded-lg p-6">
            {/* Basic Settings */}
            <div>
              <h3 className="text-lg font-medium leading-6 text-text-primary mb-4">Basic Settings</h3>

              <div className="grid grid-cols-1 gap-6">
                <Input
                  label="Rule Name"
                  id="name"
                  name="name"
                  type="text"
                  required
                  value={formData.name || ""}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />

                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Priority"
                    id="priority"
                    name="priority"
                    type="number"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                    helperText="Higher priority rules run first"
                  />

                  <div className="flex items-center pt-6">
                    <input
                      type="checkbox"
                      id="enabled"
                      checked={formData.enabled}
                      onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-border rounded"
                    />
                    <label htmlFor="enabled" className="ml-2 block text-sm text-text-primary">
                      Rule is enabled
                    </label>
                  </div>
                </div>

                {rule.match_count > 0 && (
                  <div className="bg-primary-50 border border-primary-200 rounded-md p-4">
                    <p className="text-sm text-primary-800">
                      This rule has matched {rule.match_count} transaction{rule.match_count !== 1 ? "s" : ""} so far.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Conditions */}
            <div className="border-t border-border pt-6">
              <h3 className="text-lg font-medium leading-6 text-text-primary mb-4">Conditions</h3>
              <p className="text-sm text-text-secondary mb-4">Define when this rule should match a transaction</p>

              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-2">
                    <Input
                      label="Payee Pattern"
                      id="payee_pattern"
                      name="payee_pattern"
                      type="text"
                      value={formData.payee_pattern || ""}
                      onChange={(e) => setFormData({ ...formData, payee_pattern: e.target.value })}
                      placeholder="e.g., AMAZON, STARBUCKS"
                    />
                  </div>
                  <Select
                    label="Match Type"
                    id="payee_match_type"
                    name="payee_match_type"
                    value={formData.payee_match_type || MatchType.CONTAINS}
                    onChange={(e) => setFormData({ ...formData, payee_match_type: e.target.value as MatchType })}
                  >
                    <option value={MatchType.CONTAINS}>Contains</option>
                    <option value={MatchType.STARTS_WITH}>Starts with</option>
                    <option value={MatchType.ENDS_WITH}>Ends with</option>
                    <option value={MatchType.EXACT}>Exact match</option>
                    <option value={MatchType.REGEX}>Regex</option>
                  </Select>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-2">
                    <Input
                      label="Description Pattern"
                      id="description_pattern"
                      name="description_pattern"
                      type="text"
                      value={formData.description_pattern || ""}
                      onChange={(e) => setFormData({ ...formData, description_pattern: e.target.value })}
                      placeholder="e.g., groceries, gas"
                    />
                  </div>
                  <Select
                    label="Match Type"
                    id="description_match_type"
                    name="description_match_type"
                    value={formData.description_match_type || MatchType.CONTAINS}
                    onChange={(e) => setFormData({ ...formData, description_match_type: e.target.value as MatchType })}
                  >
                    <option value={MatchType.CONTAINS}>Contains</option>
                    <option value={MatchType.STARTS_WITH}>Starts with</option>
                    <option value={MatchType.ENDS_WITH}>Ends with</option>
                    <option value={MatchType.EXACT}>Exact match</option>
                    <option value={MatchType.REGEX}>Regex</option>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Minimum Amount"
                    id="amount_min"
                    name="amount_min"
                    type="number"
                    step="0.01"
                    value={formData.amount_min || ""}
                    onChange={(e) => setFormData({ ...formData, amount_min: e.target.value })}
                    placeholder="0.00"
                  />
                  <Input
                    label="Maximum Amount"
                    id="amount_max"
                    name="amount_max"
                    type="number"
                    step="0.01"
                    value={formData.amount_max || ""}
                    onChange={(e) => setFormData({ ...formData, amount_max: e.target.value })}
                    placeholder="0.00"
                  />
                </div>

                <Select
                  label="Transaction Type"
                  id="transaction_type"
                  name="transaction_type"
                  value={formData.transaction_type || ""}
                  onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value as TransactionTypeFilter || undefined })}
                >
                  <option value="">Any</option>
                  <option value={TransactionTypeFilter.DEBIT}>Debit</option>
                  <option value={TransactionTypeFilter.CREDIT}>Credit</option>
                  <option value={TransactionTypeFilter.TRANSFER}>Transfer</option>
                </Select>
              </div>
            </div>

            {/* Actions */}
            <div className="border-t border-border pt-6">
              <h3 className="text-lg font-medium leading-6 text-text-primary mb-4">Actions</h3>
              <p className="text-sm text-text-secondary mb-4">What should happen when this rule matches?</p>

              <div className="space-y-4">
                <Select
                  label="Assign Category"
                  id="category_id"
                  name="category_id"
                  value={formData.category_id || ""}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value ? parseInt(e.target.value) : undefined })}
                >
                  <option value="">None</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </Select>

                <Input
                  label="Rename Payee To"
                  id="new_payee"
                  name="new_payee"
                  type="text"
                  value={formData.new_payee || ""}
                  onChange={(e) => setFormData({ ...formData, new_payee: e.target.value })}
                  placeholder="e.g., Amazon"
                />

                <Textarea
                  label="Append to Notes"
                  id="notes_append"
                  name="notes_append"
                  rows={3}
                  value={formData.notes_append || ""}
                  onChange={(e) => setFormData({ ...formData, notes_append: e.target.value })}
                  placeholder="Add notes to matching transactions"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3 pt-6 border-t border-border">
              <button
                type="button"
                onClick={() => router.push("/dashboard/rules")}
                className="inline-flex items-center px-4 py-2 border border-border shadow-sm text-sm font-medium rounded-md text-text-secondary bg-surface hover:bg-surface-secondary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-text-inverse bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}
