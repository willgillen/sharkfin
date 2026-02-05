"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { accountsAPI, reportsAPI } from "@/lib/api";
import { Account, SpendingByCategoryResponse, IncomeVsExpensesResponse, NetWorthHistoryResponse, SpendingTrendsResponse, IncomeExpenseDetailResponse, CashFlowForecastResponse, SankeyDiagramResponse, DashboardSummary } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import ReportHeader from "@/components/reports/ReportHeader";
import { DateRange, getDefaultDateRange } from "@/components/reports/DateRangePicker";
import CategorySpendingChart from "@/components/charts/CategorySpendingChart";
import IncomeTrendChart from "@/components/charts/IncomeTrendChart";
import NetWorthChart from "@/components/charts/NetWorthChart";
import SpendingTrendsChart from "@/components/charts/SpendingTrendsChart";
import CashFlowForecastChart from "@/components/charts/CashFlowForecastChart";
import SankeyDiagramChart from "@/components/charts/SankeyDiagramChart";
import { formatCurrency, formatPercentage, formatMonthYear } from "@/lib/utils/format";
import { exportToPdf } from "@/lib/utils/exportPdf";

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
    available: true,
  },
  {
    id: "sankey",
    name: "Money Flow",
    description: "Visualize income to expenses",
    icon: "🌊",
    available: true,
  },
];

// Wrap in Suspense for useSearchParams
export default function ReportsPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="min-h-screen flex items-center justify-center">
          <p className="text-text-secondary">Loading...</p>
        </div>
      </DashboardLayout>
    }>
      <ReportsPageContent />
    </Suspense>
  );
}

function ReportsPageContent() {
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
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [spendingData, setSpendingData] = useState<SpendingByCategoryResponse | null>(null);
  const [spendingTrendsData, setSpendingTrendsData] = useState<SpendingTrendsResponse | null>(null);
  const [incomeData, setIncomeData] = useState<IncomeVsExpensesResponse | null>(null);
  const [incomeDetailData, setIncomeDetailData] = useState<IncomeExpenseDetailResponse | null>(null);
  const [netWorthData, setNetWorthData] = useState<NetWorthHistoryResponse | null>(null);
  const [cashFlowData, setCashFlowData] = useState<CashFlowForecastResponse | null>(null);
  const [sankeyData, setSankeyData] = useState<SankeyDiagramResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

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
      // Load dashboard data for overview (includes budget status, account summary)
      if (activeReport === "overview") {
        const dashboard = await reportsAPI.getDashboard(dateRange.startDate, dateRange.endDate);
        setDashboardData(dashboard);
      }

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

      if (activeReport === "cash-flow") {
        const cashFlow = await reportsAPI.getCashFlowForecast(
          6, // historical months to analyze
          6, // forecast months
          selectedAccountId || undefined
        );
        setCashFlowData(cashFlow);
      }

      if (activeReport === "sankey") {
        const sankey = await reportsAPI.getSankeyDiagram(
          dateRange.startDate,
          dateRange.endDate,
          selectedAccountId || undefined
        );
        setSankeyData(sankey);
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

  // Handle click on category chart to drill down to transactions
  const handleCategoryDrillDown = (categoryId: number, categoryName: string) => {
    // Navigate to transactions page filtered by this category
    const params = new URLSearchParams({
      category_id: categoryId.toString(),
    });
    // If we have a date range, include it
    if (dateRange.startDate && dateRange.endDate) {
      params.set("start_date", dateRange.startDate);
      params.set("end_date", dateRange.endDate);
    }
    router.push(`/dashboard/transactions?${params.toString()}`);
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const reportName = REPORT_NAV.find((r) => r.id === activeReport)?.name || "Report";
      const dateRangeText = `${dateRange.startDate} to ${dateRange.endDate}`;
      const accountName = selectedAccountId
        ? accounts.find((a) => a.id === selectedAccountId)?.name
        : "All Accounts";
      const subtitle = `${dateRangeText} | ${accountName}`;

      await exportToPdf("report-content", {
        filename: `${activeReport}-report-${dateRange.startDate}-${dateRange.endDate}.pdf`,
        title: reportName,
        subtitle: subtitle,
      });
    } catch (err: any) {
      console.error("Export error:", err);
      setError("Failed to export report to PDF");
    } finally {
      setExporting(false);
    }
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
              Dashboard
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
            title={REPORT_NAV.find((r) => r.id === activeReport)?.name || "Dashboard"}
            description={REPORT_NAV.find((r) => r.id === activeReport)?.description}
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
            accounts={accounts}
            selectedAccountId={selectedAccountId}
            onAccountChange={setSelectedAccountId}
            accountsLoading={accountsLoading}
            showAccountFilter={true}
            actions={
              <button
                onClick={handleExport}
                disabled={loading || exporting}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {exporting ? (
                  <>
                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Exporting...
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    Export PDF
                  </>
                )}
              </button>
            }
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
            <div id="report-content" className="bg-white">
              {/* Overview Report */}
              {activeReport === "overview" && (
                <div className="space-y-6">
                  {/* Account Summary - Net Worth */}
                  {dashboardData && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-surface rounded-lg shadow p-4">
                        <div className="text-sm font-medium text-text-tertiary">Total Assets</div>
                        <div className="mt-1 text-2xl font-bold text-success-600">
                          {formatCurrency(dashboardData.account_summary.total_assets)}
                        </div>
                      </div>
                      <div className="bg-surface rounded-lg shadow p-4">
                        <div className="text-sm font-medium text-text-tertiary">Total Liabilities</div>
                        <div className="mt-1 text-2xl font-bold text-danger-600">
                          {formatCurrency(dashboardData.account_summary.total_liabilities)}
                        </div>
                      </div>
                      <div className="bg-surface rounded-lg shadow p-4">
                        <div className="text-sm font-medium text-text-tertiary">Net Worth</div>
                        <div className="mt-1 text-2xl font-bold text-primary-600">
                          {formatCurrency(dashboardData.account_summary.net_worth)}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Income vs Expenses Summary Cards */}
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

                  {/* Budget Status */}
                  {dashboardData && dashboardData.budget_status.length > 0 && (
                    <div className="bg-surface rounded-lg shadow p-6">
                      <h3 className="text-lg font-semibold text-text-primary mb-4">
                        Budget Status
                      </h3>
                      <div className="space-y-4">
                        {dashboardData.budget_status.map((budget) => (
                          <div key={budget.budget_id}>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="font-medium text-text-primary">
                                {budget.budget_name}
                              </span>
                              <span className="text-text-secondary">
                                {formatCurrency(budget.spent)} / {formatCurrency(budget.amount)}
                              </span>
                            </div>
                            <div className="w-full bg-surface-secondary rounded-full h-2.5">
                              <div
                                className={`h-2.5 rounded-full ${
                                  budget.is_over_budget
                                    ? "bg-danger-600"
                                    : parseFloat(budget.percentage) >= parseFloat(budget.alert_threshold)
                                    ? "bg-warning-500"
                                    : "bg-success-600"
                                }`}
                                style={{ width: `${Math.min(parseFloat(budget.percentage), 100)}%` }}
                              ></div>
                            </div>
                            <p className="text-xs text-text-tertiary mt-1">
                              {formatPercentage(budget.percentage)} used
                              {budget.is_over_budget && " - Over budget!"}
                            </p>
                          </div>
                        ))}
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
                        <p className="text-xs text-text-tertiary mb-2">
                          Click a category to view transactions
                        </p>
                        <CategorySpendingChart
                          data={spendingData.categories}
                          onCategoryClick={handleCategoryDrillDown}
                        />
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
                  {/* Summary Cards with Month-over-Month Change */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Total Spending</div>
                      <div className="mt-1 text-2xl font-bold text-danger-600">
                        {formatCurrency(spendingData.total_spending)}
                      </div>
                      {/* Month-over-month change calculation from trends data */}
                      {spendingTrendsData && spendingTrendsData.months.length >= 2 && (() => {
                        const months = spendingTrendsData.months;
                        const currentMonth = months[months.length - 1];
                        const prevMonth = months[months.length - 2];

                        // Calculate total spending for each month
                        let currentTotal = 0;
                        let prevTotal = 0;
                        spendingTrendsData.categories.forEach(cat => {
                          cat.monthly_data.forEach(md => {
                            if (md.month === currentMonth) currentTotal += parseFloat(md.amount);
                            if (md.month === prevMonth) prevTotal += parseFloat(md.amount);
                          });
                        });

                        const change = prevTotal > 0 ? ((currentTotal - prevTotal) / prevTotal) * 100 : 0;
                        const isIncrease = change > 0;

                        return (
                          <div className={`mt-1 text-sm flex items-center gap-1 ${isIncrease ? "text-danger-600" : "text-success-600"}`}>
                            {isIncrease ? (
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                              </svg>
                            ) : (
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            )}
                            <span>{Math.abs(change).toFixed(1)}% vs last month</span>
                          </div>
                        );
                      })()}
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
                      <p className="text-xs text-text-tertiary mb-2">
                        Click a category to view transactions
                      </p>
                      <CategorySpendingChart
                        data={spendingData.categories}
                        onCategoryClick={handleCategoryDrillDown}
                      />
                    </div>

                    {/* Average Spending by Category with Month-over-Month Change */}
                    {spendingTrendsData && (
                      <div className="bg-surface rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-text-primary mb-4">
                          Monthly Averages & Trends
                        </h3>
                        <div className="space-y-3">
                          {spendingTrendsData.categories.slice(0, 8).map((category, index) => {
                            // Calculate month-over-month change for this category
                            const months = spendingTrendsData.months;
                            let momChange = 0;
                            if (months.length >= 2) {
                              const currentMonth = months[months.length - 1];
                              const prevMonth = months[months.length - 2];
                              const currentAmount = parseFloat(category.monthly_data.find(m => m.month === currentMonth)?.amount || "0");
                              const prevAmount = parseFloat(category.monthly_data.find(m => m.month === prevMonth)?.amount || "0");
                              momChange = prevAmount > 0 ? ((currentAmount - prevAmount) / prevAmount) * 100 : 0;
                            }

                            return (
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
                                <div className="flex items-center gap-3">
                                  <span className="text-sm font-medium text-text-primary">
                                    {formatCurrency(category.average_amount)}/mo
                                  </span>
                                  {months.length >= 2 && (
                                    <span className={`text-xs flex items-center gap-0.5 ${momChange > 0 ? "text-danger-500" : momChange < 0 ? "text-success-500" : "text-text-tertiary"}`}>
                                      {momChange > 0 ? (
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                        </svg>
                                      ) : momChange < 0 ? (
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                      ) : null}
                                      {Math.abs(momChange).toFixed(0)}%
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
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
                              MoM Change
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

                            // Calculate month-over-month change
                            let momChange: number | null = null;
                            if (trendCategory && spendingTrendsData && spendingTrendsData.months.length >= 2) {
                              const months = spendingTrendsData.months;
                              const currentMonth = months[months.length - 1];
                              const prevMonth = months[months.length - 2];
                              const currentAmount = parseFloat(trendCategory.monthly_data.find(m => m.month === currentMonth)?.amount || "0");
                              const prevAmount = parseFloat(trendCategory.monthly_data.find(m => m.month === prevMonth)?.amount || "0");
                              momChange = prevAmount > 0 ? ((currentAmount - prevAmount) / prevAmount) * 100 : (currentAmount > 0 ? 100 : 0);
                            }

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
                                <td className="px-6 py-4 text-sm text-right">
                                  {momChange !== null ? (
                                    <span className={`inline-flex items-center gap-1 ${momChange > 0 ? "text-danger-600" : momChange < 0 ? "text-success-600" : "text-text-tertiary"}`}>
                                      {momChange > 0 && (
                                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                        </svg>
                                      )}
                                      {momChange < 0 && (
                                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                      )}
                                      {momChange === 0 ? "—" : `${momChange > 0 ? "+" : ""}${momChange.toFixed(1)}%`}
                                    </span>
                                  ) : (
                                    "-"
                                  )}
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
                                {formatMonthYear(month.month)}
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
                            const savingsRate = 'savings_rate' in month ? (month.savings_rate as string) : null;
                            return (
                              <tr key={month.month} className="hover:bg-surface-secondary">
                                <td className="px-6 py-4 text-sm font-medium text-text-primary">
                                  {formatMonthYear(month.month, { month: "long", year: "numeric" })}
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

              {/* Cash Flow Forecast Report */}
              {activeReport === "cash-flow" && cashFlowData && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Current Balance</div>
                      <div className="mt-1 text-2xl font-bold text-primary-600">
                        {formatCurrency(cashFlowData.current_balance)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Avg Monthly Income</div>
                      <div className="mt-1 text-2xl font-bold text-success-600">
                        {formatCurrency(cashFlowData.avg_monthly_income)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Avg Monthly Expenses</div>
                      <div className="mt-1 text-2xl font-bold text-danger-600">
                        {formatCurrency(cashFlowData.avg_monthly_expenses)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Avg Monthly Net</div>
                      <div
                        className={`mt-1 text-2xl font-bold ${
                          parseFloat(cashFlowData.avg_monthly_net) >= 0
                            ? "text-success-600"
                            : "text-danger-600"
                        }`}
                      >
                        {formatCurrency(cashFlowData.avg_monthly_net)}
                      </div>
                    </div>
                  </div>

                  {/* Forecast Chart */}
                  <div className="bg-surface rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-text-primary mb-4">
                      Cash Flow Projection
                    </h3>
                    <p className="text-sm text-text-tertiary mb-4">
                      Based on {cashFlowData.historical_months_used} months of historical data
                    </p>
                    <CashFlowForecastChart
                      projections={cashFlowData.projections}
                      currentBalance={cashFlowData.current_balance}
                    />
                  </div>

                  {/* Confidence Legend */}
                  <div className="bg-surface rounded-lg shadow p-4">
                    <h4 className="text-sm font-semibold text-text-primary mb-3">
                      Projection Confidence
                    </h4>
                    <div className="flex gap-6">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-success-500"></div>
                        <span className="text-sm text-text-secondary">High - Low variance in historical data</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-warning-500"></div>
                        <span className="text-sm text-text-secondary">Medium - Moderate variance</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-danger-500"></div>
                        <span className="text-sm text-text-secondary">Low - High variance in data</span>
                      </div>
                    </div>
                  </div>

                  {/* Projection Table */}
                  <div className="bg-surface rounded-lg shadow">
                    <div className="p-6 border-b border-border">
                      <h3 className="text-lg font-semibold text-text-primary">
                        Monthly Projections
                      </h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-surface-secondary">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Month
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Projected Income
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Projected Expenses
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Projected Net
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Projected Balance
                            </th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-text-tertiary uppercase tracking-wider">
                              Confidence
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {cashFlowData.projections.map((projection) => (
                            <tr key={projection.month} className="hover:bg-surface-secondary">
                              <td className="px-6 py-4 text-sm font-medium text-text-primary">
                                {formatMonthYear(projection.month, { month: "long", year: "numeric" })}
                              </td>
                              <td className="px-6 py-4 text-sm text-right text-success-600">
                                {formatCurrency(projection.projected_income)}
                              </td>
                              <td className="px-6 py-4 text-sm text-right text-danger-600">
                                {formatCurrency(projection.projected_expenses)}
                              </td>
                              <td
                                className={`px-6 py-4 text-sm text-right font-medium ${
                                  parseFloat(projection.projected_net) >= 0
                                    ? "text-success-600"
                                    : "text-danger-600"
                                }`}
                              >
                                {formatCurrency(projection.projected_net)}
                              </td>
                              <td className="px-6 py-4 text-sm text-right font-semibold text-primary-600">
                                {formatCurrency(projection.projected_balance)}
                              </td>
                              <td className="px-6 py-4 text-center">
                                <span
                                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                    projection.confidence === "high"
                                      ? "bg-success-100 text-success-800"
                                      : projection.confidence === "medium"
                                      ? "bg-warning-100 text-warning-800"
                                      : "bg-danger-100 text-danger-800"
                                  }`}
                                >
                                  {projection.confidence.charAt(0).toUpperCase() +
                                    projection.confidence.slice(1)}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Recurring Bills Section */}
                  {cashFlowData.recurring_bills && cashFlowData.recurring_bills.length > 0 && (
                    <div className="bg-surface rounded-lg shadow">
                      <div className="p-6 border-b border-border">
                        <h3 className="text-lg font-semibold text-text-primary">
                          Detected Recurring Bills
                        </h3>
                        <p className="text-sm text-text-tertiary mt-1">
                          Based on patterns in your transaction history
                        </p>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="bg-surface-secondary">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                Payee
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                Category
                              </th>
                              <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                Amount
                              </th>
                              <th className="px-6 py-3 text-center text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                Frequency
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                Last Paid
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                Next Expected
                              </th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border">
                            {cashFlowData.recurring_bills.map((bill, index) => (
                              <tr key={index} className="hover:bg-surface-secondary">
                                <td className="px-6 py-4 text-sm font-medium text-text-primary">
                                  {bill.payee_name}
                                </td>
                                <td className="px-6 py-4 text-sm text-text-secondary">
                                  {bill.category_name || "-"}
                                </td>
                                <td className="px-6 py-4 text-sm text-right text-danger-600 font-medium">
                                  {formatCurrency(bill.typical_amount)}
                                </td>
                                <td className="px-6 py-4 text-center">
                                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                    bill.frequency === "monthly"
                                      ? "bg-blue-100 text-blue-800"
                                      : bill.frequency === "quarterly"
                                      ? "bg-purple-100 text-purple-800"
                                      : "bg-amber-100 text-amber-800"
                                  }`}>
                                    {bill.frequency.charAt(0).toUpperCase() + bill.frequency.slice(1)}
                                  </span>
                                </td>
                                <td className="px-6 py-4 text-sm text-text-secondary">
                                  {bill.last_paid
                                    ? new Date(bill.last_paid).toLocaleDateString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric"
                                      })
                                    : "-"}
                                </td>
                                <td className="px-6 py-4 text-sm">
                                  {bill.next_expected ? (
                                    <span className={
                                      new Date(bill.next_expected) <= new Date()
                                        ? "text-danger-600 font-medium"
                                        : new Date(bill.next_expected) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
                                        ? "text-warning-600 font-medium"
                                        : "text-text-secondary"
                                    }>
                                      {new Date(bill.next_expected).toLocaleDateString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric"
                                      })}
                                      {new Date(bill.next_expected) <= new Date() && " (Due!)"}
                                      {new Date(bill.next_expected) > new Date() &&
                                        new Date(bill.next_expected) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) &&
                                        " (Soon)"}
                                    </span>
                                  ) : "-"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot className="bg-surface-secondary">
                            <tr>
                              <td colSpan={2} className="px-6 py-3 text-sm font-semibold text-text-primary">
                                Monthly Total (estimated)
                              </td>
                              <td className="px-6 py-3 text-sm text-right font-bold text-danger-600">
                                {formatCurrency(
                                  cashFlowData.recurring_bills
                                    .filter(b => b.frequency === "monthly")
                                    .reduce((sum, b) => sum + parseFloat(b.typical_amount), 0)
                                    .toString()
                                )}
                              </td>
                              <td colSpan={3}></td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Sankey / Money Flow Report */}
              {activeReport === "sankey" && sankeyData && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Total Income</div>
                      <div className="mt-1 text-2xl font-bold text-success-600">
                        {formatCurrency(sankeyData.total_income)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Total Expenses</div>
                      <div className="mt-1 text-2xl font-bold text-danger-600">
                        {formatCurrency(sankeyData.total_expenses)}
                      </div>
                    </div>
                    <div className="bg-surface rounded-lg shadow p-4">
                      <div className="text-sm font-medium text-text-tertiary">Net Savings</div>
                      <div
                        className={`mt-1 text-2xl font-bold ${
                          parseFloat(sankeyData.net_savings) >= 0
                            ? "text-primary-600"
                            : "text-danger-600"
                        }`}
                      >
                        {formatCurrency(sankeyData.net_savings)}
                      </div>
                    </div>
                  </div>

                  {/* Sankey Diagram */}
                  <div className="bg-surface rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-text-primary mb-2">
                      Money Flow Diagram
                    </h3>
                    <p className="text-sm text-text-tertiary mb-6">
                      Shows how income flows through to expenses and savings for the selected period
                    </p>
                    <div className="overflow-x-auto">
                      <SankeyDiagramChart
                        nodes={sankeyData.nodes}
                        links={sankeyData.links}
                      />
                    </div>
                  </div>

                  {/* Legend */}
                  <div className="bg-surface rounded-lg shadow p-4">
                    <h4 className="text-sm font-semibold text-text-primary mb-3">
                      How to Read This Chart
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-text-secondary">
                      <div className="flex items-start gap-2">
                        <div className="w-4 h-4 rounded bg-success-500 mt-0.5 flex-shrink-0"></div>
                        <span><strong>Green nodes</strong> represent income sources on the left</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-4 h-4 rounded bg-danger-500 mt-0.5 flex-shrink-0"></div>
                        <span><strong>Red nodes</strong> represent expense categories on the right</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-4 h-4 rounded bg-primary-500 mt-0.5 flex-shrink-0"></div>
                        <span><strong>Blue node</strong> represents net savings (income - expenses)</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-4 h-4 rounded bg-gray-300 mt-0.5 flex-shrink-0"></div>
                        <span><strong>Flow width</strong> represents the relative size of money movement</span>
                      </div>
                    </div>
                  </div>

                  {/* Breakdown Tables */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Income Sources */}
                    <div className="bg-surface rounded-lg shadow">
                      <div className="p-4 border-b border-border">
                        <h3 className="text-lg font-semibold text-success-600">Income Sources</h3>
                      </div>
                      <div className="p-4 space-y-2">
                        {sankeyData.nodes
                          .filter((n) => n.id.startsWith("income_"))
                          .map((node) => (
                            <div
                              key={node.id}
                              className="flex justify-between items-center py-2 border-b border-border last:border-0"
                            >
                              <span className="text-text-primary">{node.name}</span>
                              <span className="font-semibold text-success-600">
                                {formatCurrency(node.value)}
                              </span>
                            </div>
                          ))}
                        {sankeyData.nodes.filter((n) => n.id.startsWith("income_")).length === 0 && (
                          <p className="text-text-tertiary text-sm">No income recorded</p>
                        )}
                      </div>
                    </div>

                    {/* Expense Categories */}
                    <div className="bg-surface rounded-lg shadow">
                      <div className="p-4 border-b border-border">
                        <h3 className="text-lg font-semibold text-danger-600">Expense Categories</h3>
                      </div>
                      <div className="p-4 space-y-2">
                        {sankeyData.nodes
                          .filter((n) => n.id.startsWith("expense_"))
                          .sort((a, b) => parseFloat(b.value) - parseFloat(a.value))
                          .map((node) => (
                            <div
                              key={node.id}
                              className="flex justify-between items-center py-2 border-b border-border last:border-0"
                            >
                              <span className="text-text-primary">{node.name}</span>
                              <span className="font-semibold text-danger-600">
                                {formatCurrency(node.value)}
                              </span>
                            </div>
                          ))}
                        {sankeyData.nodes.filter((n) => n.id.startsWith("expense_")).length === 0 && (
                          <p className="text-text-tertiary text-sm">No expenses recorded</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
