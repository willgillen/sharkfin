import apiClient from "./client";
import { Transaction, TransactionCreate, TransactionUpdate } from "@/types";

export const transactionsAPI = {
  async getAll(): Promise<Transaction[]> {
    const { data } = await apiClient.get<Transaction[]>("/api/v1/transactions");
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
};
