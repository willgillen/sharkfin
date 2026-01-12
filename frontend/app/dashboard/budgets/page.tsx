"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { budgetsAPI, categoriesAPI } from "@/lib/api";
import { BudgetWithProgress, Category, BudgetPeriod } from "@/types";
import { formatCurrency, formatPercentage, formatDate } from "@/lib/utils/format";
import DashboardLayout from "@/components/layout/DashboardLayout";

export default function BudgetsPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [budgets, setBudgets] = useState<BudgetWithProgress[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [cats, budgetIds] = await Promise.all([
        categoriesAPI.getAll(),
        budgetsAPI.getAll(),
      ]);
      setCategories(cats);

      // Load budget progress for each budget
      const budgetsWithProgress = await Promise.all(
        budgetIds.map(budget => budgetsAPI.getProgress(budget.id))
      );
      setBudgets(budgetsWithProgress);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load budgets");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this budget?")) {
      return;
    }

    try {
      await budgetsAPI.delete(id);
      setBudgets(budgets.filter((b) => b.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete budget");
    }
  };

  const getCategoryName = (categoryId: number): string => {
    return categories.find((c) => c.id === categoryId)?.name || "Unknown";
  };

  const getBudgetPeriodLabel = (period: BudgetPeriod): string => {
    const labels: Record<BudgetPeriod, string> = {
      [BudgetPeriod.WEEKLY]: "Weekly",
      [BudgetPeriod.MONTHLY]: "Monthly",
      [BudgetPeriod.QUARTERLY]: "Quarterly",
      [BudgetPeriod.YEARLY]: "Yearly",
    };
    return labels[period];
  };

  const getProgressColor = (budget: BudgetWithProgress): string => {
    if (budget.is_over_budget) return "bg-red-600";
    if (parseFloat(budget.percentage) >= parseFloat(budget.alert_threshold)) {
      return "bg-yellow-500";
    }
    return "bg-green-600";
  };

  const getProgressTextColor = (budget: BudgetWithProgress): string => {
    if (budget.is_over_budget) return "text-red-600";
    if (parseFloat(budget.percentage) >= parseFloat(budget.alert_threshold)) {
      return "text-yellow-600";
    }
    return "text-green-600";
  };

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Budgets</h1>
          <button
            onClick={() => router.push("/dashboard/budgets/new")}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            + Add Budget
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading budgets...</p>
          </div>
        ) : budgets.length > 0 ? (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {budgets.map((budget) => (
              <div key={budget.id} className="bg-white shadow rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{budget.name}</h3>
                    <p className="text-sm text-gray-500">
                      {getCategoryName(budget.category_id)} • {getBudgetPeriodLabel(budget.period)}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => router.push(`/dashboard/budgets/${budget.id}`)}
                      className="text-blue-600 hover:text-blue-900 text-sm"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(budget.id)}
                      className="text-red-600 hover:text-red-900 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Budget</span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(budget.amount)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Spent</span>
                    <span className={getProgressTextColor(budget)}>
                      {formatCurrency(budget.spent)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Remaining</span>
                    <span className={getProgressTextColor(budget)}>
                      {formatCurrency(budget.remaining)}
                    </span>
                  </div>
                </div>

                <div className="mb-3">
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${getProgressColor(budget)}`}
                      style={{ width: `${Math.min(parseFloat(budget.percentage), 100)}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatPercentage(budget.percentage)} used
                    {budget.is_over_budget && " - Over budget!"}
                  </p>
                </div>

                <div className="flex justify-between text-xs text-gray-500 border-t pt-3">
                  <span>
                    {budget.start_date && `Started ${formatDate(budget.start_date)}`}
                  </span>
                  {budget.end_date && <span>Ends {formatDate(budget.end_date)}</span>}
                  {!budget.end_date && <span>No end date</span>}
                </div>

                {budget.alert_enabled && (
                  <div className="mt-2 text-xs text-gray-500">
                    Alert at {formatPercentage(budget.alert_threshold)}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-600 mb-4">No budgets yet</p>
            <button
              onClick={() => router.push("/dashboard/budgets/new")}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              + Create Your First Budget
            </button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
