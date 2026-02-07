import apiClient from "./client";
import {
  CategorizationRule,
  CategorizationRuleCreate,
  CategorizationRuleUpdate,
  RuleTestRequest,
  RuleTestResponse,
  BulkApplyRulesRequest,
  BulkApplyRulesResponse,
  RuleSuggestion,
  SuggestRulesRequest,
  AcceptSuggestionRequest,
} from "@/types";

export const rulesAPI = {
  async getAll(enabledOnly: boolean = false): Promise<CategorizationRule[]> {
    const params = enabledOnly ? { enabled_only: true } : {};
    const { data } = await apiClient.get<CategorizationRule[]>("/v1/rules", { params });
    return data;
  },

  async getById(id: number): Promise<CategorizationRule> {
    const { data } = await apiClient.get<CategorizationRule>(`/api/v1/rules/${id}`);
    return data;
  },

  async create(ruleData: CategorizationRuleCreate): Promise<CategorizationRule> {
    const { data } = await apiClient.post<CategorizationRule>("/v1/rules", ruleData);
    return data;
  },

  async update(id: number, ruleData: CategorizationRuleUpdate): Promise<CategorizationRule> {
    const { data } = await apiClient.put<CategorizationRule>(`/api/v1/rules/${id}`, ruleData);
    return data;
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/rules/${id}`);
  },

  async test(id: number, testRequest: RuleTestRequest): Promise<RuleTestResponse> {
    const { data } = await apiClient.post<RuleTestResponse>(`/api/v1/rules/${id}/test`, testRequest);
    return data;
  },

  async applyRules(request: BulkApplyRulesRequest): Promise<BulkApplyRulesResponse> {
    const { data} = await apiClient.post<BulkApplyRulesResponse>("/v1/rules/apply", request);
    return data;
  },

  async getSuggestions(request: SuggestRulesRequest = {}): Promise<RuleSuggestion[]> {
    const { data } = await apiClient.post<RuleSuggestion[]>("/v1/rules/suggestions", request);
    return data;
  },

  async acceptSuggestion(request: AcceptSuggestionRequest): Promise<CategorizationRule> {
    const { data } = await apiClient.post<CategorizationRule>("/v1/rules/suggestions/accept", request);
    return data;
  },
};
