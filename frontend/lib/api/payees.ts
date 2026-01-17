import apiClient from "./client";
import { Payee, PayeeCreate, PayeeUpdate, PayeeWithCategory, PayeeSuggestion } from "@/types";

export const payeesAPI = {
  async getAll(params?: {
    skip?: number;
    limit?: number;
    q?: string;
  }): Promise<Payee[]> {
    const { data } = await apiClient.get<Payee[]>("/api/v1/payees", { params });
    return data;
  },

  async getById(id: number): Promise<Payee> {
    const { data } = await apiClient.get<Payee>(`/api/v1/payees/${id}`);
    return data;
  },

  async create(payeeData: PayeeCreate): Promise<Payee> {
    const { data } = await apiClient.post<Payee>("/api/v1/payees", payeeData);
    return data;
  },

  async update(id: number, payeeData: PayeeUpdate): Promise<Payee> {
    const { data } = await apiClient.put<Payee>(`/api/v1/payees/${id}`, payeeData);
    return data;
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/payees/${id}`);
  },

  async autocomplete(query: string, limit: number = 10): Promise<PayeeWithCategory[]> {
    const { data } = await apiClient.get<PayeeWithCategory[]>("/api/v1/payees/autocomplete", {
      params: { q: query, limit },
    });
    return data;
  },
};
