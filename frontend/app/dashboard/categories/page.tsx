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
      [CategoryType.INCOME]: "bg-green-100 text-green-800",
      [CategoryType.EXPENSE]: "bg-red-100 text-red-800",
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
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Categories</h1>
          <button
            onClick={() => router.push("/dashboard/categories/new")}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            + Add Category
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Type Filter */}
        <div className="mb-6 bg-white shadow rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter by Type
          </label>
          <div className="flex space-x-4">
            <button
              onClick={() => setTypeFilter("")}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                typeFilter === ""
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              All Categories
            </button>
            <button
              onClick={() => setTypeFilter(CategoryType.INCOME)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                typeFilter === CategoryType.INCOME
                  ? "bg-green-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Income
            </button>
            <button
              onClick={() => setTypeFilter(CategoryType.EXPENSE)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                typeFilter === CategoryType.EXPENSE
                  ? "bg-red-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Expense
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading categories...</p>
          </div>
        ) : filteredCategories.length > 0 ? (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Parent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Color
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    System
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredCategories.map((category) => (
                  <tr key={category.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {category.icon && (
                          <span className="mr-2 text-lg">{category.icon}</span>
                        )}
                        <div className="text-sm font-medium text-gray-900">
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getParentCategoryName(category.parent_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {category.color && (
                        <div className="flex items-center">
                          <div
                            className="w-6 h-6 rounded border border-gray-300"
                            style={{ backgroundColor: category.color }}
                          ></div>
                          <span className="ml-2 text-xs text-gray-500">
                            {category.color}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {category.is_system ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                          System
                        </span>
                      ) : (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                          Custom
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => router.push(`/dashboard/categories/${category.id}`)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                        disabled={category.is_system}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(category.id)}
                        className={`${
                          category.is_system
                            ? "text-gray-400 cursor-not-allowed"
                            : "text-red-600 hover:text-red-900"
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
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-600 mb-4">
              {categories.length === 0
                ? "No categories yet"
                : "No categories match your filter"}
            </p>
            {categories.length === 0 && (
              <button
                onClick={() => router.push("/dashboard/categories/new")}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
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
