"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { accountsAPI, reportsAPI } from "@/lib/api";
import { Account, SpendingByCategoryResponse, IncomeVsExpensesResponse, NetWorthHistoryResponse, SpendingTrendsResponse, IncomeExpenseDetailResponse } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import ReportHeader from "@/components/reports/ReportHeader";
import { DateRange, getDefaultDateRange } from "@/components/reports/DateRangePicker";
import CategorySpendingChart from "@/components/charts/CategorySpendingChart";
import IncomeTrendChart from "@/components/charts/IncomeTrendChart";
import NetWorthChart from "@/components/charts/NetWorthChart";
import SpendingTrendsChart from "@/components/charts/SpendingTrendsChart";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";

type ReportType = "overview" | "spending" | "income" | "net-worth" | "cash-flow" | "sankey";

interface ReportNavItem {
  id: ReportType;
  name: string;
  description: string;
  icon: string;
  available: boolean;
}

const REPORT_NAV: ReportNavItem[] = [
  {
    id: "overview",
    name: "Overview",
    description: "Summary of all key metrics",
    icon: "📊",
    available: true,
  },
  {
    id: "spending",
    name: "Spending Trends",
    description: "Analyze spending by category",
    icon: "💸",
    available: true,
  },
  {
    id: "income",
    name: "Income vs Expenses",
    description: "Track cash flow over time",
    icon: "📈",
    available: true,
  },
  {
    id: "net-worth",
    name: "Net Worth",
    description: "Track wealth over time",
    icon: "💰",
    available: true,
  },
  {
    id: "cash-flow",
    name: "Cash Flow Forecast",
    description: "Project future balances",
    icon: "🔮",
    available: false, // Coming soon
  },
  {
    id: "sankey",
    name: "Money Flow",
    description: "Visualize income to expenses",
    icon: "🌊",
    available: false, // Coming soon
  },
];

export default function ReportsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, loading: authLoading } = useAuth();

  // State
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [dateRange, setDateRange] = useState<DateRange>(getDefaultDateRange());
  const [activeReport, setActiveReport] = useState<ReportType>("overview");

  // Report data
  const [spendingData, setSpendingData] = useState<SpendingByCategoryResponse | null>(null);
  const [spendingTrendsData, setSpendingTrendsData] = useState<SpendingTrendsResponse | null>(null);
  const [incomeData, setIncomeData] = useState<IncomeVsExpensesResponse | null>(null);
  const [incomeDetailData, setIncomeDetailData] = useState<IncomeExpenseDetailResponse | null>(null);
  const [netWorthData, setNetWorthData] = useState<NetWorthHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Auth redirect
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  // Initialize from URL params
  useEffect(() => {
    const reportParam = searchParams.get("report") as ReportType | null;
    if (reportParam && REPORT_NAV.some((r) => r.id === reportParam && r.available)) {
      setActiveReport(reportParam);
    }
  }, [searchParams]);

  // Load accounts
  useEffect(() => {
    if (isAuthenticated) {
      loadAccounts();
    }
  }, [isAuthenticated]);

  // Load report data when filters change
  useEffect(() => {
    if (isAuthenticated && dateRange.startDate && dateRange.endDate) {
      loadReportData();
    }
  }, [isAuthenticated, dateRange, selectedAccountId, activeReport]);

  const loadAccounts = async () => {
    try {
      setAccountsLoading(true);
      const data = await accountsAPI.getAll();
      setAccounts(data);
    } catch (err) {
      console.error("Failed to load accounts:", err);
    } finally {
      setAccountsLoading(false);
    }
  };

  const loadReportData = async () => {
    setLoading(true);
    setError("");

    try {
      // Load data based on active report
      if (activeReport === "overview" || activeReport === "spending") {
        const spending = await reportsAPI.getSpendingByCategory(
          dateRange.startDate,
          dateRange.endDate
        );
        setSpendingData(spending);

        // Also load spending trends for the spending report
        if (activeReport === "spending") {
          const start = new Date(dateRange.startDate);
          const end = new Date(dateRange.endDate);
          const months = Math.max(
            1,
            Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24 * 30))
          );
          const trends = await reportsAPI.getSpendingTrends(
            Math.min(months, 24),
            undefined,
            selectedAccountId || undefined
          );
          setSpendingTrendsData(trends);
        }
      }

      if (activeReport === "overview" || activeReport === "income") {
        // Calculate months from date range
        const start = new Date(dateRange.startDate);
        const end = new Date(dateRange.endDate);
        const months = Math.max(
          1,
          Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24 * 30))
        );
        const income = await reportsAPI.getIncomeVsExpenses(Math.min(months, 24));
        setIncomeData(income);

        // Also load detailed income data for the income report
        if (activeReport === "income") {
          const incomeDetail = await reportsAPI.getIncomeExpenseDetail(
            Math.min(months, 24),
            selectedAccountId || undefined
          );
          setIncomeDetailData(incomeDetail);
        }
      }

      if (activeReport === "net-worth") {
        // Calculate months from date range
        const start = new Date(dateRange.startDate);
        const end = new Date(dateRange.endDate);
        const months = Math.max(
          1,
          Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24 * 30))
        );
        const netWorth = await reportsAPI.getNetWorthHistory(
          Math.min(months, 60),
          selectedAccountId || undefined
        );
        setNetWorthData(netWorth);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load report data");
    } finally {
      setLoading(false);
    }
  };

  const handleReportChange = (reportId: ReportType) => {
    setActiveReport(reportId);
    router.replace(`/dashboard/reports?report=${reportId}`, { scroll: false });
  };

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-secondary">Loading...</p>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex gap-6">
        {/* Sidebar Navigation */}
        <div className="w-64 flex-shrink-0">
          <div className="bg-surface rounded-lg shadow p-4 sticky top-6">
            <h2 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider mb-3">
              Reports
            </h2>
            <nav className="space-y-1">
              {REPORT_NAV.map((item) => (
                <button
                  key={item.id}
                  onClick={() => item.available && handleReportChange(item.id)}
                  disabled={!item.available}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    activeReport === item.id
                      ? "bg-primary-100 text-primary-700"
                      : item.available
                      ? "text-text-primary hover:bg-surface-secondary"
                      : "text-text-disabled cursor-not-allowed"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{item.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">
                        {item.name}
                        {!item.available && (
                          <span className="ml-2 text-xs text-text-tertiary">(Coming Soon)</span>
                        )}
                      </div>
                      <div className="text-xs text-text-tertiary truncate">{item.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <ReportHeader
            title={REPORT_NAV.find((r) => r.id === activeReport)?.name || "Reports"}
            description={REPORT_NAV.find((r) => r.id === activeReport)?.description}
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
            accounts={accounts}
            selectedAccountId={selectedAccountId}
            onAccountChange={setSelectedAccountId}
            accountsLoading={accountsLoading}
            showAccountFilter={true}
          />

          {error && (
            <div className="mb-4 rounded-md bg-danger-50 p-4">
              <p className="text-sm text-danger-800">{error}</p>
            </div>
          )}

          {loading ? (
            <div className="text-center py-12">
              <p className="text-text-secondary">Loading report data...</p>
            </div>
          ) : (
            <>
              {/* Overview Report */}
              {activeReport === "overview" && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  {incomeData && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="bg-surface rounded-lg shadow p-4">
                        <div className="text-sm font-medium text-text-tertiary">Total Income</div>
                        <div className="mt-1 text-2xl font-bold text-success-600">
                          {formatCurrency(incomeData.current_period.total_income)}
                        </div>
                      </div>
                      <div className="bg-surface rounded-lg shadow p-4">
                        <div className="text-sm font-medium text-text-tertiary">Total Expenses</div>
                        <div className="mt-1 text-2xl font-bold text-danger-600">
                          {formatCurrency(incomeData.current_period.total_expenses)}
                        </div>
                      </div>
                      <div className="bg-surface rounded-lg shadow p-4">
                        <div className="text-sm font-medium text-text-tertiary">Net</div>
                        <div
                          className={`mt-1 text-2xl font-bold ${
                            parseFloat(incomeData.current_period.net) >= 0
                              ? "text-success-600"
                              : "text-danger-600"
                          }`}
                        >
                          {formatCurrency(incomeData.current_period.net)}
                        </div>
                      </div>
                      <div className="bg-surface rounded-lg shadow p-4">
                        <div className="text-sm font-medium text-text-tertiary">Savings Rate</div>
                        <div className="mt-1 text-2xl font-bold text-primary-600">
                          {formatPercentage(incomeData.current_period.savings_rate)}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Charts Row */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Spending by Category */}
                    {spendingData && (
                      <div className="bg-surface rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-text-primary mb-4">
                          Spending by Category
                        </h3>
                        <CategorySpendingChart data={spendingData.categories} />
                      </div>
                    )}

                    {/* Income vs Expenses Trend */}
                    {incomeData && (
                      <div className="bg-surface rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-text-primary mb-4">
                          Income vs Expenses
                        </h3>
                        <IncomeTrendChart data={incomeData.monthly_trends} />
                      </div>
                    )}
                  </div>

                  {/* Top Spending Categories Table */}
                  {spendingData && spendingData.categories.length > 0 && (
                    <div className="bg-surface rounded-lg shadow">
                      <div className="p-6 border-b border-border">
                        <h3 className="text-lg font-semibold text-text-primary">
                          Top Spending Categories
                        </h3>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="bg-surface-secondary">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                Category
                              </th>
                              <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                Amount
                              </th>
                              <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                % of Total
                              </th>
                              <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                Transactions
                              </th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border">
                            {spendingData.categories.slice(0, 10).map((category) => (
                              <tr key={category.category_id} className="hover:bg-surface-secondary">
                                <td className="px-6 py-4 text-sm font-medium text-text-primary">
                                  {category.category_name}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-text-primary">
                                  {formatCurrency(category.amount)}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-text-secondary">
                                  {formatPercentage(category.percentage)}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-text-tertiary">
                                  {category.transaction_count}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot className="bg-surface-secondary">
                            <tr>
                              <td className="px-6 py-3 text-sm font-semibold text-text-primary">
                                Total
                              </td>
                              <td className="px-6 py-3 text-sm font-semibold text-right text-text-primary">
                                {formatCurrency(spendingData.total_spending)}
                              </td>
                              <td className="px-6 py-3 text-sm text-right text-text-secondary">
                                100%
                              </td>
                              <td className="px-6 py-3 text-sm text-right text-text-tertiary">
                                {spendingData.categories.reduce(
                                  (sum, c) => sum + c.transaction_count,
                                  0
                                )}
                              </td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Spending Trends Report */}
              {activeReport === "spending" && spendingData && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Total Spending</div>
                      <div className="mt-1 text-2xl font-bold text-danger-600">
                        {formatCurrency(spendingData.total_spending)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Categories</div>
                      <div className="mt-1 text-2xl font-bold text-text-primary">
                        {spendingData.categories.length}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Transactions</div>
                      <div className="mt-1 text-2xl font-bold text-text-primary">
                        {spendingData.categories.reduce((sum, c) => sum + c.transaction_count, 0)}
                      </div>
                    </div>
                  </div>

                  {/* Spending Trends Over Time */}
                  {spendingTrendsData && (
                    <div className="bg-surface rounded-lg shadow p-6">
                      <h3 className="text-lg font-semibold text-text-primary mb-4">
                        Spending Trends Over Time
                      </h3>
                      <SpendingTrendsChart
                        data={spendingTrendsData.categories}
                        months={spendingTrendsData.months}
                      />
                    </div>
                  )}

                  {/* Charts Row */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Pie Chart */}
                    <div className="bg-surface rounded-lg shadow p-6">
                      <h3 className="text-lg font-semibold text-text-primary mb-4">
                        Spending by Category
                      </h3>
                      <CategorySpendingChart data={spendingData.categories} />
                    </div>

                    {/* Average Spending by Category */}
                    {spendingTrendsData && (
                      <div className="bg-surface rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-text-primary mb-4">
                          Monthly Averages
                        </h3>
                        <div className="space-y-3">
                          {spendingTrendsData.categories.slice(0, 8).map((category, index) => (
                            <div key={category.category_id} className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <div
                                  className="w-3 h-3 rounded-full"
                                  style={{
                                    backgroundColor: [
                                      "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
                                      "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"
                                    ][index % 8]
                                  }}
                                />
                                <span className="text-sm text-text-primary">{category.category_name}</span>
                              </div>
                              <span className="text-sm font-medium text-text-primary">
                                {formatCurrency(category.average_amount)}/mo
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Category Details Table */}
                  <div className="bg-surface rounded-lg shadow">
                    <div className="p-6 border-b border-border">
                      <h3 className="text-lg font-semibold text-text-primary">Category Details</h3>
                      <p className="text-sm text-text-secondary mt-1">
                        Total spending: {formatCurrency(spendingData.total_spending)}
                      </p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-surface-secondary">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Category
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Amount
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Avg/Month
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              % of Total
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Transactions
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Progress
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {spendingData.categories.map((category) => {
                            const trendCategory = spendingTrendsData?.categories.find(
                              (c) => c.category_id === category.category_id
                            );
                            return (
                              <tr key={category.category_id} className="hover:bg-surface-secondary">
                                <td className="px-6 py-4 text-sm font-medium text-text-primary">
                                  {category.category_name}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-text-primary">
                                  {formatCurrency(category.amount)}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-text-secondary">
                                  {trendCategory
                                    ? formatCurrency(trendCategory.average_amount)
                                    : "-"}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-text-secondary">
                                  {formatPercentage(category.percentage)}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-text-tertiary">
                                  {category.transaction_count}
                                </td>
                                <td className="px-6 py-4">
                                  <div className="w-full bg-surface-secondary rounded-full h-2">
                                    <div
                                      className="bg-primary-600 h-2 rounded-full"
                                      style={{ width: `${Math.min(parseFloat(category.percentage), 100)}%` }}
                                    ></div>
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Income vs Expenses Report */}
              {activeReport === "income" && incomeData && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Total Income</div>
                      <div className="mt-1 text-2xl font-bold text-success-600">
                        {formatCurrency(incomeData.current_period.total_income)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Total Expenses</div>
                      <div className="mt-1 text-2xl font-bold text-danger-600">
                        {formatCurrency(incomeData.current_period.total_expenses)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Net</div>
                      <div
                        className={`mt-1 text-2xl font-bold ${
                          parseFloat(incomeData.current_period.net) >= 0
                            ? "text-success-600"
                            : "text-danger-600"
                        }`}
                      >
                        {formatCurrency(incomeData.current_period.net)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Savings Rate</div>
                      <div className="mt-1 text-2xl font-bold text-primary-600">
                        {formatPercentage(incomeData.current_period.savings_rate)}
                      </div>
                    </div>
                  </div>

                  {/* Trend Chart */}
                  <div className="bg-surface rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-text-primary mb-4">Monthly Trends</h3>
                    <div className="h-96">
                      <IncomeTrendChart data={incomeData.monthly_trends} />
                    </div>
                  </div>

                  {/* Income Sources and Top Expenses */}
                  {incomeDetailData && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Income Sources */}
                      <div className="bg-surface rounded-lg shadow">
                        <div className="p-4 border-b border-border">
                          <h3 className="text-lg font-semibold text-success-600">Income Sources</h3>
                        </div>
                        <div className="p-4">
                          {incomeDetailData.income_by_source.length > 0 ? (
                            <>
                              {incomeDetailData.income_by_source.map((source) => (
                                <div
                                  key={source.category_id}
                                  className="flex justify-between items-center py-2 border-b border-border last:border-0"
                                >
                                  <div className="flex-1">
                                    <div className="font-medium text-text-primary">
                                      {source.category_name}
                                    </div>
                                    <div className="text-xs text-text-tertiary">
                                      {source.transaction_count} transactions ({formatPercentage(source.percentage)})
                                    </div>
                                  </div>
                                  <div className="font-semibold text-success-600">
                                    {formatCurrency(source.amount)}
                                  </div>
                                </div>
                              ))}
                              <div className="flex justify-between items-center pt-4 mt-2 border-t border-border">
                                <div className="font-semibold text-text-primary">Total Income</div>
                                <div className="font-bold text-success-600">
                                  {formatCurrency(incomeDetailData.summary.total_income)}
                                </div>
                              </div>
                            </>
                          ) : (
                            <p className="text-text-tertiary text-sm">No income recorded</p>
                          )}
                        </div>
                      </div>

                      {/* Savings Rate Trend */}
                      <div className="bg-surface rounded-lg shadow">
                        <div className="p-4 border-b border-border">
                          <h3 className="text-lg font-semibold text-primary-600">Monthly Savings Rate</h3>
                        </div>
                        <div className="p-4">
                          {incomeDetailData.monthly_breakdown.map((month) => (
                            <div
                              key={month.month}
                              className="flex items-center gap-4 py-2 border-b border-border last:border-0"
                            >
                              <div className="w-24 text-sm text-text-primary">
                                {new Date(month.month + "-01").toLocaleDateString("en-US", {
                                  month: "short",
                                  year: "2-digit",
                                })}
                              </div>
                              <div className="flex-1">
                                <div className="w-full bg-surface-secondary rounded-full h-4">
                                  <div
                                    className={`h-4 rounded-full ${
                                      parseFloat(month.savings_rate) >= 0
                                        ? "bg-primary-500"
                                        : "bg-danger-500"
                                    }`}
                                    style={{
                                      width: `${Math.min(Math.abs(parseFloat(month.savings_rate)), 100)}%`,
                                    }}
                                  />
                                </div>
                              </div>
                              <div
                                className={`w-16 text-right text-sm font-medium ${
                                  parseFloat(month.savings_rate) >= 0
                                    ? "text-primary-600"
                                    : "text-danger-600"
                                }`}
                              >
                                {formatPercentage(month.savings_rate)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Monthly Breakdown Table */}
                  <div className="bg-surface rounded-lg shadow">
                    <div className="p-6 border-b border-border">
                      <h3 className="text-lg font-semibold text-text-primary">Monthly Breakdown</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-surface-secondary">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Month
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Income
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Expenses
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Net
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Savings Rate
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {(incomeDetailData?.monthly_breakdown || incomeData.monthly_trends).map((month) => {
                            const savingsRate = 'savings_rate' in month ? month.savings_rate : null;
                            return (
                              <tr key={month.month} className="hover:bg-surface-secondary">
                                <td className="px-6 py-4 text-sm font-medium text-text-primary">
                                  {new Date(month.month + "-01").toLocaleDateString("en-US", {
                                    month: "long",
                                    year: "numeric",
                                  })}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-success-600">
                                  {formatCurrency(month.income)}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-danger-600">
                                  {formatCurrency(month.expenses)}
                                </td>
                                <td
                                  className={`px-6 py-4 text-sm text-right font-medium ${
                                    parseFloat(month.net) >= 0 ? "text-success-600" : "text-danger-600"
                                  }`}
                                >
                                  {formatCurrency(month.net)}
                                </td>
                                <td
                                  className={`px-6 py-4 text-sm text-right ${
                                    savingsRate && parseFloat(savingsRate) >= 0
                                      ? "text-primary-600"
                                      : "text-danger-600"
                                  }`}
                                >
                                  {savingsRate ? formatPercentage(savingsRate) : "-"}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Net Worth Report */}
              {activeReport === "net-worth" && netWorthData && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Total Assets</div>
                      <div className="mt-1 text-2xl font-bold text-success-600">
                        {formatCurrency(netWorthData.current.total_assets)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Total Liabilities</div>
                      <div className="mt-1 text-2xl font-bold text-danger-600">
                        {formatCurrency(netWorthData.current.total_liabilities)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Net Worth</div>
                      <div
                        className={`mt-1 text-2xl font-bold ${
                          parseFloat(netWorthData.current.net_worth) >= 0
                            ? "text-success-600"
                            : "text-danger-600"
                        }`}
                      >
                        {formatCurrency(netWorthData.current.net_worth)}
                      </div>
                    </div>
                  </div>

                  {/* Net Worth History Chart */}
                  <div className="bg-surface rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-text-primary mb-4">
                      Net Worth Over Time
                    </h3>
                    <NetWorthChart data={netWorthData.history} />
                  </div>

                  {/* Accounts Breakdown */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Assets */}
                    <div className="bg-surface rounded-lg shadow">
                      <div className="p-4 border-b border-border">
                        <h3 className="text-lg font-semibold text-success-600">Assets</h3>
                      </div>
                      <div className="p-4">
                        {netWorthData.accounts
                          .filter((a) => a.is_asset)
                          .map((account) => (
                            <div
                              key={account.account_id}
                              className="flex justify-between items-center py-2 border-b border-border last:border-0"
                            >
                              <div>
                                <div className="font-medium text-text-primary">
                                  {account.account_name}
                                </div>
                                <div className="text-xs text-text-tertiary capitalize">
                                  {account.account_type.replace("_", " ")}
                                </div>
                              </div>
                              <div className="font-semibold text-success-600">
                                {formatCurrency(account.balance)}
                              </div>
                            </div>
                          ))}
                        {netWorthData.accounts.filter((a) => a.is_asset).length === 0 && (
                          <p className="text-text-tertiary text-sm">No asset accounts</p>
                        )}
                        <div className="flex justify-between items-center pt-4 mt-2 border-t border-border">
                          <div className="font-semibold text-text-primary">Total Assets</div>
                          <div className="font-bold text-success-600">
                            {formatCurrency(netWorthData.current.total_assets)}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Liabilities */}
                    <div className="bg-surface rounded-lg shadow">
                      <div className="p-4 border-b border-border">
                        <h3 className="text-lg font-semibold text-danger-600">Liabilities</h3>
                      </div>
                      <div className="p-4">
                        {netWorthData.accounts
                          .filter((a) => !a.is_asset)
                          .map((account) => (
                            <div
                              key={account.account_id}
                              className="flex justify-between items-center py-2 border-b border-border last:border-0"
                            >
                              <div>
                                <div className="font-medium text-text-primary">
                                  {account.account_name}
                                </div>
                                <div className="text-xs text-text-tertiary capitalize">
                                  {account.account_type.replace("_", " ")}
                                </div>
                              </div>
                              <div className="font-semibold text-danger-600">
                                {formatCurrency(Math.abs(parseFloat(account.balance)))}
                              </div>
                            </div>
                          ))}
                        {netWorthData.accounts.filter((a) => !a.is_asset).length === 0 && (
                          <p className="text-text-tertiary text-sm">No liability accounts</p>
                        )}
                        <div className="flex justify-between items-center pt-4 mt-2 border-t border-border">
                          <div className="font-semibold text-text-primary">Total Liabilities</div>
                          <div className="font-bold text-danger-600">
                            {formatCurrency(netWorthData.current.total_liabilities)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Net Worth History Table */}
                  <div className="bg-surface rounded-lg shadow">
                    <div className="p-6 border-b border-border">
                      <h3 className="text-lg font-semibold text-text-primary">Monthly History</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-surface-secondary">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Date
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Assets
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Liabilities
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Net Worth
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Change
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {netWorthData.history.map((point, index) => {
                            const prevPoint = index > 0 ? netWorthData.history[index - 1] : null;
                            const change = prevPoint
                              ? parseFloat(point.net_worth) - parseFloat(prevPoint.net_worth)
                              : 0;
                            return (
                              <tr key={point.date} className="hover:bg-surface-secondary">
                                <td className="px-6 py-4 text-sm font-medium text-text-primary">
                                  {new Date(point.date).toLocaleDateString("en-US", {
                                    month: "long",
                                    year: "numeric",
                                  })}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-success-600">
                                  {formatCurrency(point.total_assets)}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-danger-600">
                                  {formatCurrency(point.total_liabilities)}
                                </td>
                                <td
                                  className={`px-6 py-4 text-sm text-right font-semibold ${
                                    parseFloat(point.net_worth) >= 0
                                      ? "text-success-600"
                                      : "text-danger-600"
                                  }`}
                                >
                                  {formatCurrency(point.net_worth)}
                                </td>
                                <td
                                  className={`px-6 py-4 text-sm text-right ${
                                    change >= 0 ? "text-success-600" : "text-danger-600"
                                  }`}
                                >
                                  {index > 0 ? (
                                    <>
                                      {change >= 0 ? "+" : ""}
                                      {formatCurrency(change.toString())}
                                    </>
                                  ) : (
                                    "-"
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Coming Soon Reports */}
              {(activeReport === "cash-flow" ||
                activeReport === "sankey") && (
                <div className="bg-surface rounded-lg shadow p-12 text-center">
                  <div className="text-6xl mb-4">
                    {REPORT_NAV.find((r) => r.id === activeReport)?.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-text-primary mb-2">Coming Soon</h3>
                  <p className="text-text-secondary max-w-md mx-auto">
                    The {REPORT_NAV.find((r) => r.id === activeReport)?.name} report is currently
                    under development. Check back soon!
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
