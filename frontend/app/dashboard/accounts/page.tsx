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
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Accounts</h1>
          <button
            onClick={() => router.push("/dashboard/accounts/new")}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            + Add Account
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading accounts...</p>
          </div>
        ) : accounts.length > 0 ? (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Account
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Institution
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Balance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {accounts.map((account) => (
                  <tr key={account.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {account.name}
                      </div>
                      {account.account_number && (
                        <div className="text-sm text-gray-500">
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {account.institution || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                      <span
                        className={
                          parseFloat(account.current_balance) >= 0
                            ? "text-green-600"
                            : "text-red-600"
                        }
                      >
                        {formatCurrency(account.current_balance, account.currency)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          account.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {account.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => router.push(`/dashboard/accounts/${account.id}`)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(account.id)}
                        className="text-red-600 hover:text-red-900"
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
            <p className="text-gray-600 mb-4">No accounts yet</p>
            <button
              onClick={() => router.push("/dashboard/accounts/new")}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              + Add Your First Account
            </button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
