import apiClient from "./client";
import { Budget, BudgetCreate, BudgetUpdate, BudgetWithProgress } from "@/types";

export const budgetsAPI = {
  async getAll(): Promise<Budget[]> {
    const { data } = await apiClient.get<Budget[]>("/v1/budgets");
    return data;
  },

  async getById(id: number): Promise<Budget> {
    const { data } = await apiClient.get<Budget>(`/api/v1/budgets/${id}`);
    return data;
  },

  async getProgress(id: number): Promise<BudgetWithProgress> {
    const { data } = await apiClient.get<BudgetWithProgress>(`/api/v1/budgets/${id}/progress`);
    return data;
  },

  async create(budgetData: BudgetCreate): Promise<Budget> {
    const { data } = await apiClient.post<Budget>("/v1/budgets", budgetData);
    return data;
  },

  async update(id: number, budgetData: BudgetUpdate): Promise<Budget> {
    const { data } = await apiClient.put<Budget>(`/api/v1/budgets/${id}`, budgetData);
    return data;
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/budgets/${id}`);
  },
};
