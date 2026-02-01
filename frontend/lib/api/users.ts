import apiClient from "./client";
import { User, UserPreferences, PreferencesMetadata } from "@/types";

export const usersAPI = {
  async getMe(): Promise<User> {
    const { data } = await apiClient.get<User>("/api/v1/users/me");
    return data;
  },

  // Preference endpoints
  async getPreferences(): Promise<UserPreferences> {
    const { data } = await apiClient.get<UserPreferences>("/api/v1/users/me/preferences");
    return data;
  },

  async getPreferencesMetadata(): Promise<PreferencesMetadata> {
    const { data } = await apiClient.get<PreferencesMetadata>("/api/v1/users/me/preferences/metadata");
    return data;
  },

  async getPreferencesByCategory(category: string): Promise<Partial<UserPreferences>> {
    const { data } = await apiClient.get<Partial<UserPreferences>>(`/api/v1/users/me/preferences/${category}`);
    return data;
  },

  async updatePreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    const { data } = await apiClient.patch<UserPreferences>("/api/v1/users/me/preferences", preferences);
    return data;
  },

  async resetPreference(key: string): Promise<{ message: string }> {
    const { data } = await apiClient.delete<{ message: string }>(`/api/v1/users/me/preferences/${key}`);
    return data;
  },

  async resetAllPreferences(): Promise<{ message: string }> {
    const { data } = await apiClient.delete<{ message: string }>("/api/v1/users/me/preferences");
    return data;
  },

  async resetCategoryPreferences(category: string): Promise<{ message: string }> {
    const { data } = await apiClient.delete<{ message: string }>(`/api/v1/users/me/preferences/category/${category}`);
    return data;
  },
};
