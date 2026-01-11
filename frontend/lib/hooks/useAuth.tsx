"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { User, LoginCredentials, UserCreate } from "@/types";
import { authAPI } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const currentUser = await authAPI.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      localStorage.removeItem("access_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials) => {
    const tokenData = await authAPI.login(credentials);
    localStorage.setItem("access_token", tokenData.access_token);
    const currentUser = await authAPI.getCurrentUser();
    setUser(currentUser);
  };

  const register = async (userData: UserCreate) => {
    const newUser = await authAPI.register(userData);
    const credentials: LoginCredentials = {
      username: userData.email,
      password: userData.password,
    };
    await login(credentials);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
    authAPI.logout();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
