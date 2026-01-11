"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { reportsAPI } from "@/lib/api";
import { DashboardSummary } from "@/types";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import DashboardLayout from "@/components/layout/DashboardLayout";

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboard();
    }
  }, [isAuthenticated]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await reportsAPI.getDashboard();
      setDashboard(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
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
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading dashboard...</p>
          </div>
        ) : dashboard ? (
          <div className="space-y-6">
            {/* Account Summary */}
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-1">
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Assets
                      </dt>
                      <dd className="mt-1 text-3xl font-semibold text-green-600">
                        {formatCurrency(dashboard.account_summary.total_assets)}
                      </dd>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-1">
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Liabilities
                      </dt>
                      <dd className="mt-1 text-3xl font-semibold text-red-600">
                        {formatCurrency(dashboard.account_summary.total_liabilities)}
                      </dd>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-1">
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Net Worth
                      </dt>
                      <dd className="mt-1 text-3xl font-semibold text-blue-600">
                        {formatCurrency(dashboard.account_summary.net_worth)}
                      </dd>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Income vs Expenses */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Income vs Expenses
              </h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
                <div>
                  <p className="text-sm text-gray-500">Total Income</p>
                  <p className="text-2xl font-semibold text-green-600">
                    {formatCurrency(dashboard.income_vs_expenses.total_income)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Expenses</p>
                  <p className="text-2xl font-semibold text-red-600">
                    {formatCurrency(dashboard.income_vs_expenses.total_expenses)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Net</p>
                  <p className={`text-2xl font-semibold ${
                    parseFloat(dashboard.income_vs_expenses.net) >= 0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}>
                    {formatCurrency(dashboard.income_vs_expenses.net)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Savings Rate</p>
                  <p className="text-2xl font-semibold text-blue-600">
                    {formatPercentage(dashboard.income_vs_expenses.savings_rate)}
                  </p>
                </div>
              </div>
            </div>

            {/* Budget Status */}
            {dashboard.budget_status.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Budget Status
                </h2>
                <div className="space-y-4">
                  {dashboard.budget_status.map((budget) => (
                    <div key={budget.budget_id}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-gray-700">
                          {budget.budget_name}
                        </span>
                        <span className="text-gray-500">
                          {formatCurrency(budget.spent)} / {formatCurrency(budget.amount)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className={`h-2.5 rounded-full ${
                            budget.is_over_budget
                              ? "bg-red-600"
                              : parseFloat(budget.percentage) >= parseFloat(budget.alert_threshold)
                              ? "bg-yellow-500"
                              : "bg-green-600"
                          }`}
                          style={{ width: `${Math.min(parseFloat(budget.percentage), 100)}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatPercentage(budget.percentage)} used
                        {budget.is_over_budget && " - Over budget!"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Spending Categories */}
            {dashboard.top_spending_categories.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Top Spending Categories
                </h2>
                <div className="space-y-3">
                  {dashboard.top_spending_categories.map((category) => (
                    <div key={category.category_id} className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-700">
                          {category.category_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {category.transaction_count} transactions
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900">
                          {formatCurrency(category.amount)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatPercentage(category.percentage)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600">No data available</p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
