"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { accountsAPI } from "@/lib/api";
import { Account, AccountType } from "@/types";
import { formatCurrency, formatDate } from "@/lib/utils/format";
import DashboardLayout from "@/components/layout/DashboardLayout";

export default function AccountsPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadAccounts();
    }
  }, [isAuthenticated]);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      const data = await accountsAPI.getAll();
      setAccounts(data);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load accounts");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this account?")) {
      return;
    }

    try {
      await accountsAPI.delete(id);
      setAccounts(accounts.filter((a) => a.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete account");
    }
  };

  const getAccountTypeLabel = (type: AccountType): string => {
    const labels: Record<AccountType, string> = {
      [AccountType.CHECKING]: "Checking",
      [AccountType.SAVINGS]: "Savings",
      [AccountType.CREDIT_CARD]: "Credit Card",
      [AccountType.LOAN]: "Loan",
      [AccountType.INVESTMENT]: "Investment",
      [AccountType.CASH]: "Cash",
      [AccountType.OTHER]: "Other",
    };
    return labels[type];
  };

  const getAccountTypeColor = (type: AccountType): string => {
    const colors: Record<AccountType, string> = {
      [AccountType.CHECKING]: "bg-blue-100 text-blue-800",
      [AccountType.SAVINGS]: "bg-green-100 text-green-800",
      [AccountType.CREDIT_CARD]: "bg-red-100 text-red-800",
      [AccountType.LOAN]: "bg-orange-100 text-orange-800",
      [AccountType.INVESTMENT]: "bg-purple-100 text-purple-800",
      [AccountType.CASH]: "bg-gray-100 text-gray-800",
      [AccountType.OTHER]: "bg-yellow-100 text-yellow-800",
    };
    return colors[type];
  };

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
          <h1 className="text-3xl font-bold text-text-primary">Accounts</h1>
          <button
            onClick={() => router.push("/dashboard/accounts/new")}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
          >
            + Add Account
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-danger-50 p-4">
            <p className="text-sm text-danger-800">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <p className="text-text-secondary">Loading accounts...</p>
          </div>
        ) : accounts.length > 0 ? (
          <div className="bg-surface shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-surface-secondary">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Account
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Institution
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Balance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-surface divide-y divide-border">
                {accounts.map((account) => (
                  <tr key={account.id} className="hover:bg-surface-secondary">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-text-primary">
                        {account.name}
                      </div>
                      {account.account_number && (
                        <div className="text-sm text-text-tertiary">
                          ***{account.account_number.slice(-4)}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getAccountTypeColor(
                          account.type
                        )}`}
                      >
                        {getAccountTypeLabel(account.type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-text-tertiary">
                      {account.institution || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                      <span
                        className={
                          parseFloat(account.current_balance) >= 0
                            ? "text-success-600"
                            : "text-danger-600"
                        }
                      >
                        {formatCurrency(account.current_balance, account.currency)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          account.is_active
                            ? "bg-success-100 text-success-800"
                            : "bg-surface-tertiary text-text-secondary"
                        }`}
                      >
                        {account.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => router.push(`/dashboard/accounts/${account.id}`)}
                        className="text-primary-600 hover:text-primary-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(account.id)}
                        className="text-danger-600 hover:text-danger-900"
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
            <p className="text-text-secondary mb-4">No accounts yet</p>
            <button
              onClick={() => router.push("/dashboard/accounts/new")}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              + Add Your First Account
            </button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
