"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { categoriesAPI } from "@/lib/api";
import { CategoryCreate } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import CategoryForm from "@/components/forms/CategoryForm";

export default function NewCategoryPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = async (data: CategoryCreate) => {
    await categoriesAPI.create(data);
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

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0 max-w-3xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Create New Category</h1>
          <p className="mt-2 text-sm text-gray-600">
            Organize your transactions with custom categories.
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <CategoryForm onSubmit={handleSubmit} onCancel={handleCancel} />
        </div>
      </div>
    </DashboardLayout>
  );
}
