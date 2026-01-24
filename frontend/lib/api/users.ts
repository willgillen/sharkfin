import apiClient from "./client";
import { User } from "@/types";

export const usersAPI = {
  async getMe(): Promise<User> {
    const { data } = await apiClient.get<User>("/api/v1/users/me");
    return data;
  },

  async updatePreferences(preferences: Record<string, any>): Promise<User> {
    const { data } = await apiClient.patch<User>("/api/v1/users/me/preferences", preferences);
    return data;
  },
};
