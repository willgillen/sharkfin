import apiClient from "./client";
import { Token, LoginCredentials, User, UserCreate } from "@/types";

export const authAPI = {
  async login(credentials: LoginCredentials): Promise<Token> {
    const formData = new URLSearchParams();
    formData.append("username", credentials.username);
    formData.append("password", credentials.password);

    const { data } = await apiClient.post<Token>("/api/v1/auth/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });
    return data;
  },

  async register(userData: UserCreate): Promise<User> {
    const { data } = await apiClient.post<User>("/api/v1/auth/register", userData);
    return data;
  },

  async getCurrentUser(): Promise<User> {
    const { data } = await apiClient.get<User>("/api/v1/users/me");
    return data;
  },

  logout() {
    localStorage.removeItem("access_token");
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  },
};
