import apiClient from "./client";
import {
  Payee,
  PayeeCreate,
  PayeeUpdate,
  PayeeWithCategory,
  PayeeSuggestion,
  PayeeTransaction,
  PayeeStats,
  PayeePattern,
  PayeePatternCreate,
  PayeePatternUpdate,
  PatternTestResult,
  IconSuggestion,
  IconParsed
} from "@/types";

export const payeesAPI = {
  async getAll(params?: {
    skip?: number;
    limit?: number;
    q?: string;
  }): Promise<PayeeWithCategory[]> {
    const { data } = await apiClient.get<PayeeWithCategory[]>("/v1/payees", { params });
    return data;
  },

  async getById(id: number): Promise<Payee> {
    const { data } = await apiClient.get<Payee>(`/api/v1/payees/${id}`);
    return data;
  },

  async create(payeeData: PayeeCreate): Promise<Payee> {
    const { data } = await apiClient.post<Payee>("/v1/payees", payeeData);
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
    const { data } = await apiClient.get<PayeeWithCategory[]>("/v1/payees/autocomplete", {
      params: { q: query, limit },
    });
    return data;
  },

  async getTransactions(id: number, limit: number = 50): Promise<PayeeTransaction[]> {
    const { data } = await apiClient.get<PayeeTransaction[]>(
      `/api/v1/payees/${id}/transactions`,
      { params: { limit } }
    );
    return data;
  },

  async getStats(id: number): Promise<PayeeStats> {
    const { data } = await apiClient.get<PayeeStats>(`/api/v1/payees/${id}/stats`);
    return data;
  },

  // Pattern management
  async getPatterns(payeeId: number): Promise<PayeePattern[]> {
    const { data } = await apiClient.get<PayeePattern[]>(
      `/api/v1/payees/${payeeId}/patterns`
    );
    return data;
  },

  async createPattern(payeeId: number, patternData: PayeePatternCreate): Promise<PayeePattern> {
    const { data } = await apiClient.post<PayeePattern>(
      `/api/v1/payees/${payeeId}/patterns`,
      patternData
    );
    return data;
  },

  async updatePattern(patternId: number, patternData: PayeePatternUpdate): Promise<PayeePattern> {
    const { data } = await apiClient.put<PayeePattern>(
      `/api/v1/payees/patterns/${patternId}`,
      patternData
    );
    return data;
  },

  async deletePattern(patternId: number): Promise<void> {
    await apiClient.delete(`/api/v1/payees/patterns/${patternId}`);
  },

  async testPattern(
    patternType: string,
    patternValue: string,
    description: string
  ): Promise<PatternTestResult> {
    const { data } = await apiClient.post<PatternTestResult>(
      `/api/v1/payees/patterns/test`,
      { description },
      { params: { pattern_type: patternType, pattern_value: patternValue } }
    );
    return data;
  },

  // Icon suggestion
  async suggestIcon(name: string): Promise<IconSuggestion> {
    const { data } = await apiClient.get<IconSuggestion>(
      `/api/v1/payees/icons/suggest`,
      { params: { name } }
    );
    return data;
  },

  async parseIcon(logoUrl: string | null): Promise<IconParsed> {
    const { data } = await apiClient.get<IconParsed>(
      `/api/v1/payees/icons/parse`,
      { params: { logo_url: logoUrl } }
    );
    return data;
  },

  async listBrands(): Promise<Array<{ name: string; slug: string; color: string; url: string }>> {
    const { data } = await apiClient.get<Array<{ name: string; slug: string; color: string; url: string }>>(
      `/api/v1/payees/icons/brands`
    );
    return data;
  },
};
