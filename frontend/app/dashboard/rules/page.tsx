"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { rulesAPI, categoriesAPI } from "@/lib/api";
import {
  CategorizationRule,
  RuleSuggestion,
  Category,
  MatchType,
  TransactionTypeFilter,
} from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";

export default function RulesPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [rules, setRules] = useState<CategorizationRule[]>([]);
  const [suggestions, setSuggestions] = useState<RuleSuggestion[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [error, setError] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeTab, setActiveTab] = useState<"rules" | "suggestions">("rules");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadRules();
      loadCategories();
    }
  }, [isAuthenticated]);

  const loadRules = async () => {
    try {
      setLoading(true);
      const data = await rulesAPI.getAll();
      setRules(data);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load rules");
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

  const loadSuggestions = async () => {
    try {
      setSuggestionsLoading(true);
      const data = await rulesAPI.getSuggestions({
        min_occurrences: 3,
        min_confidence: 0.7,
      });
      setSuggestions(data);
      setActiveTab("suggestions");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to load suggestions");
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this rule?")) {
      return;
    }

    try {
      await rulesAPI.delete(id);
      setRules(rules.filter((r) => r.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete rule");
    }
  };

  const handleToggleEnabled = async (rule: CategorizationRule) => {
    try {
      const updated = await rulesAPI.update(rule.id, { enabled: !rule.enabled });
      setRules(rules.map((r) => (r.id === rule.id ? updated : r)));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to update rule");
    }
  };

  const handleAcceptSuggestion = async (suggestion: RuleSuggestion) => {
    try {
      const newRule = await rulesAPI.acceptSuggestion({
        suggested_rule_name: suggestion.suggested_rule_name,
        payee_pattern: suggestion.payee_pattern,
        payee_match_type: suggestion.payee_match_type,
        description_pattern: suggestion.description_pattern,
        description_match_type: suggestion.description_match_type,
        amount_min: suggestion.amount_min,
        amount_max: suggestion.amount_max,
        transaction_type: suggestion.transaction_type,
        category_id: suggestion.category_id,
        priority: 100,
        enabled: true,
      });

      setRules([newRule, ...rules]);
      setSuggestions(suggestions.filter((s) => s.suggested_rule_name !== suggestion.suggested_rule_name));
      alert("Rule created successfully!");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to create rule");
    }
  };

  const getCategoryName = (categoryId?: number): string => {
    if (!categoryId) return "-";
    const category = categories.find((c) => c.id === categoryId);
    return category?.name || "Unknown";
  };

  const getMatchTypeLabel = (matchType?: MatchType): string => {
    if (!matchType) return "-";
    const labels: Record<MatchType, string> = {
      [MatchType.CONTAINS]: "Contains",
      [MatchType.STARTS_WITH]: "Starts with",
      [MatchType.ENDS_WITH]: "Ends with",
      [MatchType.EXACT]: "Exact match",
      [MatchType.REGEX]: "Regex",
    };
    return labels[matchType];
  };

  if (authLoading || loading) {
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
        {/* Header */}
        <div className="sm:flex sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Categorization Rules</h1>
            <p className="mt-2 text-sm text-gray-700">
              Automatically categorize transactions based on patterns
            </p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none space-x-2">
            <button
              onClick={loadSuggestions}
              disabled={suggestionsLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              {suggestionsLoading ? "Loading..." : "Get Suggestions"}
            </button>
            <button
              onClick={() => router.push("/dashboard/rules/new")}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Create Rule
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Tabs */}
        <div className="mt-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab("rules")}
              className={`${
                activeTab === "rules"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              My Rules ({rules.length})
            </button>
            <button
              onClick={() => setActiveTab("suggestions")}
              className={`${
                activeTab === "suggestions"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Suggestions ({suggestions.length})
            </button>
          </nav>
        </div>

        {/* Rules List */}
        {activeTab === "rules" && (
          <div className="mt-8">
            {rules.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                <h3 className="text-sm font-medium text-gray-900">No rules yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by creating a rule or loading suggestions.
                </p>
                <div className="mt-6">
                  <button
                    onClick={() => router.push("/dashboard/rules/new")}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Create your first rule
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {rules.map((rule) => (
                    <li key={rule.id} className="px-6 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center">
                            <h3 className="text-sm font-medium text-gray-900">{rule.name}</h3>
                            {rule.auto_created && (
                              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                Auto-learned
                              </span>
                            )}
                            <span
                              className={`ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                rule.enabled
                                  ? "bg-green-100 text-green-800"
                                  : "bg-gray-100 text-gray-800"
                              }`}
                            >
                              {rule.enabled ? "Enabled" : "Disabled"}
                            </span>
                            <span className="ml-2 text-xs text-gray-500">
                              Priority: {rule.priority}
                            </span>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2 text-sm text-gray-500">
                            {rule.payee_pattern && (
                              <span className="inline-flex items-center">
                                <span className="font-medium">Payee:</span>
                                <span className="ml-1">
                                  {getMatchTypeLabel(rule.payee_match_type)} "{rule.payee_pattern}"
                                </span>
                              </span>
                            )}
                            {rule.category_id && (
                              <span className="inline-flex items-center">
                                <span className="font-medium">→ Category:</span>
                                <span className="ml-1">{getCategoryName(rule.category_id)}</span>
                              </span>
                            )}
                            {rule.match_count > 0 && (
                              <span className="text-xs text-gray-400">
                                ({rule.match_count} matches)
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="ml-4 flex items-center space-x-2">
                          <button
                            onClick={() => handleToggleEnabled(rule)}
                            className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                          >
                            {rule.enabled ? "Disable" : "Enable"}
                          </button>
                          <button
                            onClick={() => router.push(`/dashboard/rules/${rule.id}`)}
                            className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(rule.id)}
                            className="inline-flex items-center px-3 py-1 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Suggestions List */}
        {activeTab === "suggestions" && (
          <div className="mt-8">
            {suggestions.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                <h3 className="text-sm font-medium text-gray-900">No suggestions available</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Categorize some transactions manually, and we'll suggest rules based on your patterns.
                </p>
                <div className="mt-6">
                  <button
                    onClick={loadSuggestions}
                    disabled={suggestionsLoading}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
                  >
                    {suggestionsLoading ? "Loading..." : "Check for Suggestions"}
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {suggestions.map((suggestion, idx) => (
                    <li key={idx} className="px-6 py-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center">
                            <h3 className="text-sm font-medium text-gray-900">
                              {suggestion.suggested_rule_name}
                            </h3>
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {Math.round(suggestion.confidence_score * 100)}% confident
                            </span>
                            <span className="ml-2 text-xs text-gray-500">
                              {suggestion.match_count} transactions
                            </span>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2 text-sm text-gray-500">
                            {suggestion.payee_pattern && (
                              <span className="inline-flex items-center">
                                <span className="font-medium">Payee:</span>
                                <span className="ml-1">
                                  {getMatchTypeLabel(suggestion.payee_match_type)} "
                                  {suggestion.payee_pattern}"
                                </span>
                              </span>
                            )}
                            {suggestion.category_id && (
                              <span className="inline-flex items-center">
                                <span className="font-medium">→ Category:</span>
                                <span className="ml-1">{suggestion.category_name}</span>
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="ml-4 flex items-center space-x-2">
                          <button
                            onClick={() => handleAcceptSuggestion(suggestion)}
                            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                          >
                            Accept & Create Rule
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
