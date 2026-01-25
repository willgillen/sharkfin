"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { categoriesAPI } from "@/lib/api";
import { Category, CategoryType } from "@/types";
import { formatDate } from "@/lib/utils/format";
import DashboardLayout from "@/components/layout/DashboardLayout";

export default function CategoriesPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadCategories();
    }
  }, [isAuthenticated]);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const data = await categoriesAPI.getAll();
      setCategories(data);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load categories");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    const category = categories.find(c => c.id === id);
    if (category?.is_system) {
      alert("Cannot delete system categories");
      return;
    }

    if (!confirm("Are you sure you want to delete this category? This will affect all associated transactions.")) {
      return;
    }

    try {
      await categoriesAPI.delete(id);
      setCategories(categories.filter((c) => c.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete category");
    }
  };

  const getCategoryTypeLabel = (type: CategoryType): string => {
    const labels: Record<CategoryType, string> = {
      [CategoryType.INCOME]: "Income",
      [CategoryType.EXPENSE]: "Expense",
    };
    return labels[type];
  };

  const getCategoryTypeColor = (type: CategoryType): string => {
    const colors: Record<CategoryType, string> = {
      [CategoryType.INCOME]: "bg-success-100 text-success-800",
      [CategoryType.EXPENSE]: "bg-danger-100 text-danger-800",
    };
    return colors[type];
  };

  const getParentCategoryName = (parentId: number | null): string => {
    if (!parentId) return "-";
    return categories.find((c) => c.id === parentId)?.name || "Unknown";
  };

  const filteredCategories = categories.filter((cat) => {
    if (typeFilter && cat.type !== typeFilter) return false;
    return true;
  });

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-secondary">Loading...</p>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-text-primary">Categories</h1>
          <button
            onClick={() => router.push("/dashboard/categories/new")}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
          >
            + Add Category
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-danger-50 p-4">
            <p className="text-sm text-danger-800">{error}</p>
          </div>
        )}

        {/* Type Filter */}
        <div className="mb-6 bg-surface shadow rounded-lg p-4">
          <label className="block text-sm font-medium text-text-secondary mb-2">
            Filter by Type
          </label>
          <div className="flex space-x-4">
            <button
              onClick={() => setTypeFilter("")}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                typeFilter === ""
                  ? "bg-primary-600 text-white"
                  : "bg-surface-tertiary text-text-secondary hover:bg-surface-secondary"
              }`}
            >
              All Categories
            </button>
            <button
              onClick={() => setTypeFilter(CategoryType.INCOME)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                typeFilter === CategoryType.INCOME
                  ? "bg-success-600 text-white"
                  : "bg-surface-tertiary text-text-secondary hover:bg-surface-secondary"
              }`}
            >
              Income
            </button>
            <button
              onClick={() => setTypeFilter(CategoryType.EXPENSE)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                typeFilter === CategoryType.EXPENSE
                  ? "bg-danger-600 text-white"
                  : "bg-surface-tertiary text-text-secondary hover:bg-surface-secondary"
              }`}
            >
              Expense
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-text-secondary">Loading categories...</p>
          </div>
        ) : filteredCategories.length > 0 ? (
          <div className="bg-surface shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-surface-secondary">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Parent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Color
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    System
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-surface divide-y divide-border">
                {filteredCategories.map((category) => (
                  <tr key={category.id} className="hover:bg-surface-secondary">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {category.icon && (
                          <span className="mr-2 text-lg">{category.icon}</span>
                        )}
                        <div className="text-sm font-medium text-text-primary">
                          {category.name}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getCategoryTypeColor(
                          category.type
                        )}`}
                      >
                        {getCategoryTypeLabel(category.type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-text-tertiary">
                      {getParentCategoryName(category.parent_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {category.color && (
                        <div className="flex items-center">
                          <div
                            className="w-6 h-6 rounded border border-border"
                            style={{ backgroundColor: category.color }}
                          ></div>
                          <span className="ml-2 text-xs text-text-tertiary">
                            {category.color}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {category.is_system ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-surface-tertiary text-text-secondary">
                          System
                        </span>
                      ) : (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-primary-100 text-primary-800">
                          Custom
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => router.push(`/dashboard/categories/${category.id}`)}
                        className="text-primary-600 hover:text-primary-900 mr-4"
                        disabled={category.is_system}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(category.id)}
                        className={`${
                          category.is_system
                            ? "text-text-disabled cursor-not-allowed"
                            : "text-danger-600 hover:text-danger-900"
                        }`}
                        disabled={category.is_system}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 bg-surface rounded-lg shadow">
            <p className="text-text-secondary mb-4">
              {categories.length === 0
                ? "No categories yet"
                : "No categories match your filter"}
            </p>
            {categories.length === 0 && (
              <button
                onClick={() => router.push("/dashboard/categories/new")}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                + Create Your First Category
              </button>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
