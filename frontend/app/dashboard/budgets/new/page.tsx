"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { budgetsAPI } from "@/lib/api";
import { BudgetCreate } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import BudgetForm from "@/components/forms/BudgetForm";

export default function NewBudgetPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = async (data: BudgetCreate) => {
    await budgetsAPI.create(data);
    router.push("/dashboard/budgets");
  };

  const handleCancel = () => {
    router.push("/dashboard/budgets");
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
          <h1 className="text-3xl font-bold text-gray-900">Create New Budget</h1>
          <p className="mt-2 text-sm text-gray-600">
            Set spending limits for your expense categories.
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <BudgetForm onSubmit={handleSubmit} onCancel={handleCancel} />
        </div>
      </div>
    </DashboardLayout>
  );
}
