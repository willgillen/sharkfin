import apiClient from "./client";
import { DashboardSummary, SpendingByCategoryResponse, IncomeVsExpensesResponse, NetWorthHistoryResponse, SpendingTrendsResponse, IncomeExpenseDetailResponse, CashFlowForecastResponse, SankeyDiagramResponse } from "@/types";

export const reportsAPI = {
  async getDashboard(startDate?: string, endDate?: string): Promise<DashboardSummary> {
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    const { data } = await apiClient.get<DashboardSummary>(
      `/v1/reports/dashboard?${params.toString()}`
    );
    return data;
  },

  async getSpendingByCategory(startDate?: string, endDate?: string): Promise<SpendingByCategoryResponse> {
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    const { data } = await apiClient.get<SpendingByCategoryResponse>(
      `/v1/reports/spending-by-category?${params.toString()}`
    );
    return data;
  },

  async getIncomeVsExpenses(months: number = 6): Promise<IncomeVsExpensesResponse> {
    const { data } = await apiClient.get<IncomeVsExpensesResponse>(
      `/v1/reports/income-vs-expenses?months=${months}`
    );
    return data;
  },

  async getNetWorthHistory(months: number = 12, accountId?: number): Promise<NetWorthHistoryResponse> {
    const params = new URLSearchParams();
    params.append("months", months.toString());
    if (accountId) params.append("account_id", accountId.toString());

    const { data } = await apiClient.get<NetWorthHistoryResponse>(
      `/v1/reports/net-worth-history?${params.toString()}`
    );
    return data;
  },

  async getSpendingTrends(
    months: number = 6,
    categoryIds?: number[],
    accountId?: number
  ): Promise<SpendingTrendsResponse> {
    const params = new URLSearchParams();
    params.append("months", months.toString());
    if (categoryIds && categoryIds.length > 0) {
      params.append("category_ids", categoryIds.join(","));
    }
    if (accountId) params.append("account_id", accountId.toString());

    const { data } = await apiClient.get<SpendingTrendsResponse>(
      `/v1/reports/spending-trends?${params.toString()}`
    );
    return data;
  },

  async getIncomeExpenseDetail(
    months: number = 6,
    accountId?: number
  ): Promise<IncomeExpenseDetailResponse> {
    const params = new URLSearchParams();
    params.append("months", months.toString());
    if (accountId) params.append("account_id", accountId.toString());

    const { data } = await apiClient.get<IncomeExpenseDetailResponse>(
      `/v1/reports/income-expense-detail?${params.toString()}`
    );
    return data;
  },

  async getCashFlowForecast(
    historicalMonths: number = 6,
    forecastMonths: number = 3,
    accountId?: number
  ): Promise<CashFlowForecastResponse> {
    const params = new URLSearchParams();
    params.append("historical_months", historicalMonths.toString());
    params.append("forecast_months", forecastMonths.toString());
    if (accountId) params.append("account_id", accountId.toString());

    const { data } = await apiClient.get<CashFlowForecastResponse>(
      `/v1/reports/cash-flow-forecast?${params.toString()}`
    );
    return data;
  },

  async getSankeyDiagram(
    startDate?: string,
    endDate?: string,
    accountId?: number
  ): Promise<SankeyDiagramResponse> {
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (accountId) params.append("account_id", accountId.toString());

    const { data } = await apiClient.get<SankeyDiagramResponse>(
      `/v1/reports/sankey-diagram?${params.toString()}`
    );
    return data;
  },

  // Export functions - these trigger file downloads
  getExportUrl(
    reportType: "transactions" | "spending-by-category" | "income-vs-expenses" | "net-worth-history",
    params: Record<string, string | number | undefined>
  ): string {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    return `/v1/reports/export/${reportType}?${searchParams.toString()}`;
  },

  async exportTransactions(options?: {
    startDate?: string;
    endDate?: string;
    accountId?: number;
    categoryId?: number;
    type?: string;
    payeeSearch?: string;
  }): Promise<void> {
    const params = new URLSearchParams();
    if (options?.startDate) params.append("start_date", options.startDate);
    if (options?.endDate) params.append("end_date", options.endDate);
    if (options?.accountId) params.append("account_id", options.accountId.toString());
    if (options?.categoryId) params.append("category_id", options.categoryId.toString());
    if (options?.type) params.append("type", options.type);
    if (options?.payeeSearch) params.append("payee_search", options.payeeSearch);

    const response = await apiClient.get(`/v1/reports/export/transactions?${params.toString()}`, {
      responseType: "blob",
    });

    // Create download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;

    // Extract filename from content-disposition header
    const contentDisposition = response.headers["content-disposition"];
    const filenameMatch = contentDisposition?.match(/filename=(.+)/);
    const filename = filenameMatch ? filenameMatch[1] : "transactions.csv";

    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async exportSpendingByCategory(startDate?: string, endDate?: string): Promise<void> {
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    const response = await apiClient.get(`/v1/reports/export/spending-by-category?${params.toString()}`, {
      responseType: "blob",
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;

    const contentDisposition = response.headers["content-disposition"];
    const filenameMatch = contentDisposition?.match(/filename=(.+)/);
    const filename = filenameMatch ? filenameMatch[1] : "spending_by_category.csv";

    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async exportIncomeVsExpenses(months: number = 6): Promise<void> {
    const response = await apiClient.get(`/v1/reports/export/income-vs-expenses?months=${months}`, {
      responseType: "blob",
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;

    const contentDisposition = response.headers["content-disposition"];
    const filenameMatch = contentDisposition?.match(/filename=(.+)/);
    const filename = filenameMatch ? filenameMatch[1] : "income_vs_expenses.csv";

    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async exportNetWorthHistory(months: number = 12): Promise<void> {
    const response = await apiClient.get(`/v1/reports/export/net-worth-history?months=${months}`, {
      responseType: "blob",
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;

    const contentDisposition = response.headers["content-disposition"];
    const filenameMatch = contentDisposition?.match(/filename=(.+)/);
    const filename = filenameMatch ? filenameMatch[1] : "net_worth_history.csv";

    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
