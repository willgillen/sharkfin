"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { transactionsAPI } from "@/lib/api";
import { TransactionCreate } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import TransactionForm from "@/components/forms/TransactionForm";

export default function NewTransactionPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = async (data: TransactionCreate) => {
    await transactionsAPI.create(data);
    router.push("/dashboard/transactions");
  };

  const handleCancel = () => {
    router.push("/dashboard/transactions");
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
          <h1 className="text-3xl font-bold text-gray-900">Add New Transaction</h1>
          <p className="mt-2 text-sm text-gray-600">
            Record a new income, expense, or transfer.
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <TransactionForm onSubmit={handleSubmit} onCancel={handleCancel} />
        </div>
      </div>
    </DashboardLayout>
  );
}
