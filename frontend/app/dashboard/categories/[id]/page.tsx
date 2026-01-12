"use client";

import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { categoriesAPI } from "@/lib/api";
import { Category, CategoryUpdate } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import CategoryForm from "@/components/forms/CategoryForm";

export default function EditCategoryPage() {
  const router = useRouter();
  const params = useParams();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [category, setCategory] = useState<Category | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const categoryId = parseInt(params.id as string);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated && categoryId) {
      loadCategory();
    }
  }, [isAuthenticated, categoryId]);

  const loadCategory = async () => {
    try {
      setLoading(true);
      const data = await categoriesAPI.getById(categoryId);

      if (data.is_system) {
        setError("Cannot edit system categories");
        return;
      }

      setCategory(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load category");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (data: CategoryUpdate) => {
    await categoriesAPI.update(categoryId, data);
    router.push("/dashboard/categories");
  };

  const handleCancel = () => {
    router.push("/dashboard/categories");
  };

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-600">Loading category...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !category) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-red-600">{error || "Category not found"}</p>
          <button
            onClick={() => router.push("/dashboard/categories")}
            className="mt-4 text-blue-600 hover:text-blue-800"
          >
            Back to Categories
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0 max-w-3xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Edit Category</h1>
          <p className="mt-2 text-sm text-gray-600">
            Update your category settings.
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <CategoryForm category={category} onSubmit={handleSubmit} onCancel={handleCancel} />
        </div>
      </div>
    </DashboardLayout>
  );
}
