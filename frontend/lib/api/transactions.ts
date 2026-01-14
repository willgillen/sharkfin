import apiClient from "./client";
import { Transaction, TransactionCreate, TransactionUpdate } from "@/types";

export const transactionsAPI = {
  async getAll(params?: {
    account_id?: number;
    category_id?: number;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: string;
  }): Promise<Transaction[]> {
    const { data } = await apiClient.get<Transaction[]>("/api/v1/transactions", { params });
    return data;
  },

  async getById(id: number): Promise<Transaction> {
    const { data } = await apiClient.get<Transaction>(`/api/v1/transactions/${id}`);
    return data;
  },

  async create(transactionData: TransactionCreate): Promise<Transaction> {
    const { data } = await apiClient.post<Transaction>("/api/v1/transactions", transactionData);
    return data;
  },

  async update(id: number, transactionData: TransactionUpdate): Promise<Transaction> {
    const { data } = await apiClient.put<Transaction>(`/api/v1/transactions/${id}`, transactionData);
    return data;
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/transactions/${id}`);
  },

  async getPayeeSuggestions(query?: string): Promise<string[]> {
    const { data } = await apiClient.get<string[]>("/api/v1/transactions/suggestions/payees", {
      params: { q: query, limit: 10 },
    });
    return data;
  },

  async getCategorySuggestion(payee: string): Promise<{ category_id: number | null }> {
    const { data } = await apiClient.get<{ category_id: number | null }>(
      "/api/v1/transactions/suggestions/category",
      {
        params: { payee },
      }
    );
    return data;
  },
};
