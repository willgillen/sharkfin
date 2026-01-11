import apiClient from "./client";
import { DashboardSummary, SpendingByCategoryResponse, IncomeVsExpensesResponse } from "@/types";

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
};
