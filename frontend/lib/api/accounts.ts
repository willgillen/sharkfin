import apiClient from "./client";
import { Account, AccountCreate, AccountUpdate } from "@/types";

export const accountsAPI = {
  async getAll(): Promise<Account[]> {
    const { data } = await apiClient.get<Account[]>("/v1/accounts");
    return data;
  },

  async getById(id: number): Promise<Account> {
    const { data } = await apiClient.get<Account>(`/api/v1/accounts/${id}`);
    return data;
  },

  async create(accountData: AccountCreate): Promise<Account> {
    const { data } = await apiClient.post<Account>("/v1/accounts", accountData);
    return data;
  },

  async update(id: number, accountData: AccountUpdate): Promise<Account> {
    const { data } = await apiClient.put<Account>(`/api/v1/accounts/${id}`, accountData);
    return data;
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/accounts/${id}`);
  },
};
