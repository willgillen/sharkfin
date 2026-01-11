"use client";

import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { transactionsAPI } from "@/lib/api";
import { Transaction, TransactionUpdate } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import TransactionForm from "@/components/forms/TransactionForm";

export default function EditTransactionPage() {
  const router = useRouter();
  const params = useParams();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [transaction, setTransaction] = useState<Transaction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const transactionId = parseInt(params.id as string);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated && transactionId) {
      loadTransaction();
    }
  }, [isAuthenticated, transactionId]);

  const loadTransaction = async () => {
    try {
      setLoading(true);
      const data = await transactionsAPI.getById(transactionId);
      setTransaction(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load transaction");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (data: TransactionUpdate) => {
    await transactionsAPI.update(transactionId, data);
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

  if (loading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-600">Loading transaction...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !transaction) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-red-600">{error || "Transaction not found"}</p>
          <button
            onClick={() => router.push("/dashboard/transactions")}
            className="mt-4 text-blue-600 hover:text-blue-800"
          >
            Back to Transactions
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0 max-w-3xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Edit Transaction</h1>
          <p className="mt-2 text-sm text-gray-600">
            Update the details of this transaction.
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <TransactionForm transaction={transaction} onSubmit={handleSubmit} onCancel={handleCancel} />
        </div>
      </div>
    </DashboardLayout>
  );
}
