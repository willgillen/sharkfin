import apiClient from "./client";
import { DashboardSummary, SpendingByCategoryResponse, IncomeVsExpensesResponse, NetWorthHistoryResponse, SpendingTrendsResponse, IncomeExpenseDetailResponse } from "@/types";

export const reportsAPI = {
  async getDashboard(startDate?: string, endDate?: string): Promise<DashboardSummary> {
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    const { data } = await apiClient.get<DashboardSummary>(
      `/api/v1/reports/dashboard?${params.toString()}`
    );
    return data;
  },

  async getSpendingByCategory(startDate?: string, endDate?: string): Promise<SpendingByCategoryResponse> {
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    const { data } = await apiClient.get<SpendingByCategoryResponse>(
      `/api/v1/reports/spending-by-category?${params.toString()}`
    );
    return data;
  },

  async getIncomeVsExpenses(months: number = 6): Promise<IncomeVsExpensesResponse> {
    const { data } = await apiClient.get<IncomeVsExpensesResponse>(
      `/api/v1/reports/income-vs-expenses?months=${months}`
    );
    return data;
  },

  async getNetWorthHistory(months: number = 12, accountId?: number): Promise<NetWorthHistoryResponse> {
    const params = new URLSearchParams();
    params.append("months", months.toString());
    if (accountId) params.append("account_id", accountId.toString());

    const { data } = await apiClient.get<NetWorthHistoryResponse>(
      `/api/v1/reports/net-worth-history?${params.toString()}`
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
      `/api/v1/reports/spending-trends?${params.toString()}`
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
      `/api/v1/reports/income-expense-detail?${params.toString()}`
    );
    return data;
  },
};
