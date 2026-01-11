import apiClient from "./client";
import { Category, CategoryCreate, CategoryUpdate } from "@/types";

export const categoriesAPI = {
  async getAll(): Promise<Category[]> {
    const { data } = await apiClient.get<Category[]>("/api/v1/categories");
    return data;
  },

  async getById(id: number): Promise<Category> {
    const { data } = await apiClient.get<Category>(`/api/v1/categories/${id}`);
    return data;
  },

  async create(categoryData: CategoryCreate): Promise<Category> {
    const { data } = await apiClient.post<Category>("/api/v1/categories", categoryData);
    return data;
  },

  async update(id: number, categoryData: CategoryUpdate): Promise<Category> {
    const { data } = await apiClient.put<Category>(`/api/v1/categories/${id}`, categoryData);
    return data;
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/categories/${id}`);
  },
};
