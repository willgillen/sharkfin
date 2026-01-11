"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { accountsAPI } from "@/lib/api";
import { AccountCreate } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import AccountForm from "@/components/forms/AccountForm";

export default function NewAccountPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = async (data: AccountCreate) => {
    await accountsAPI.create(data);
    router.push("/dashboard/accounts");
  };

  const handleCancel = () => {
    router.push("/dashboard/accounts");
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
          <h1 className="text-3xl font-bold text-gray-900">Add New Account</h1>
          <p className="mt-2 text-sm text-gray-600">
            Create a new financial account to track your money.
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <AccountForm onSubmit={handleSubmit} onCancel={handleCancel} />
        </div>
      </div>
    </DashboardLayout>
  );
}
