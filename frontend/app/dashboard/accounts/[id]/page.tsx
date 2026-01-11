"use client";

import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { accountsAPI } from "@/lib/api";
import { Account, AccountUpdate } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import AccountForm from "@/components/forms/AccountForm";

export default function EditAccountPage() {
  const router = useRouter();
  const params = useParams();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const accountId = parseInt(params.id as string);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated && accountId) {
      loadAccount();
    }
  }, [isAuthenticated, accountId]);

  const loadAccount = async () => {
    try {
      setLoading(true);
      const data = await accountsAPI.getById(accountId);
      setAccount(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load account");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (data: AccountUpdate) => {
    await accountsAPI.update(accountId, data);
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

  if (loading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-600">Loading account...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !account) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-red-600">{error || "Account not found"}</p>
          <button
            onClick={() => router.push("/dashboard/accounts")}
            className="mt-4 text-blue-600 hover:text-blue-800"
          >
            Back to Accounts
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0 max-w-3xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Edit Account</h1>
          <p className="mt-2 text-sm text-gray-600">
            Update the details of your account.
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <AccountForm account={account} onSubmit={handleSubmit} onCancel={handleCancel} />
        </div>
      </div>
    </DashboardLayout>
  );
}
