"use client";

import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { budgetsAPI } from "@/lib/api";
import { Budget, BudgetUpdate } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import BudgetForm from "@/components/forms/BudgetForm";

export default function EditBudgetPage() {
  const router = useRouter();
  const params = useParams();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [budget, setBudget] = useState<Budget | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const budgetId = parseInt(params.id as string);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated && budgetId) {
      loadBudget();
    }
  }, [isAuthenticated, budgetId]);

  const loadBudget = async () => {
    try {
      setLoading(true);
      const data = await budgetsAPI.getById(budgetId);
      setBudget(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load budget");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (data: BudgetUpdate) => {
    await budgetsAPI.update(budgetId, data);
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

  if (loading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-600">Loading budget...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !budget) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-red-600">{error || "Budget not found"}</p>
          <button
            onClick={() => router.push("/dashboard/budgets")}
            className="mt-4 text-blue-600 hover:text-blue-800"
          >
            Back to Budgets
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0 max-w-3xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Edit Budget</h1>
          <p className="mt-2 text-sm text-gray-600">
            Update your budget settings and limits.
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <BudgetForm budget={budget} onSubmit={handleSubmit} onCancel={handleCancel} />
        </div>
      </div>
    </DashboardLayout>
  );
}
