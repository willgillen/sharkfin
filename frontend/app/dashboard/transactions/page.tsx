"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { transactionsAPI, accountsAPI, categoriesAPI } from "@/lib/api";
import { Transaction, Account, Category, TransactionType } from "@/types";
import { formatCurrency, formatDate } from "@/lib/utils/format";
import DashboardLayout from "@/components/layout/DashboardLayout";
import QuickAddBar from "@/components/transactions/QuickAddBar";

export default function TransactionsPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters
  const [accountFilter, setAccountFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [txns, accts, cats] = await Promise.all([
        transactionsAPI.getAll(),
        accountsAPI.getAll(),
        categoriesAPI.getAll(),
      ]);
      setTransactions(txns);
      setAccounts(accts);
      setCategories(cats);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this transaction?")) {
      return;
    }

    try {
      await transactionsAPI.delete(id);
      setTransactions(transactions.filter((t) => t.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete transaction");
    }
  };

  const getAccountName = (accountId: number): string => {
    return accounts.find((a) => a.id === accountId)?.name || "Unknown";
  };

  const getCategoryName = (categoryId: number | null): string => {
    if (!categoryId) return "Uncategorized";
    return categories.find((c) => c.id === categoryId)?.name || "Unknown";
  };

  const getTransactionTypeColor = (type: TransactionType): string => {
    const colors: Record<TransactionType, string> = {
      [TransactionType.DEBIT]: "text-red-600",
      [TransactionType.CREDIT]: "text-green-600",
      [TransactionType.TRANSFER]: "text-blue-600",
    };
    return colors[type];
  };

  const getTransactionTypeLabel = (type: TransactionType): string => {
    const labels: Record<TransactionType, string> = {
      [TransactionType.DEBIT]: "Expense",
      [TransactionType.CREDIT]: "Income",
      [TransactionType.TRANSFER]: "Transfer",
    };
    return labels[type];
  };

  const filteredTransactions = transactions.filter((txn) => {
    if (accountFilter && txn.account_id !== parseInt(accountFilter)) return false;
    if (categoryFilter && txn.category_id !== parseInt(categoryFilter)) return false;
    if (typeFilter && txn.type !== typeFilter) return false;
    return true;
  });

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
          <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
          <button
            onClick={() => router.push("/dashboard/transactions/new")}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            + Add Transaction
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Quick Add Bar */}
        <QuickAddBar onTransactionAdded={loadData} />

        {/* Filters */}
        <div className="mb-6 bg-white shadow rounded-lg p-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account
              </label>
              <select
                value={accountFilter}
                onChange={(e) => setAccountFilter(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Accounts</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Categories</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Types</option>
                <option value={TransactionType.CREDIT}>Income</option>
                <option value={TransactionType.DEBIT}>Expense</option>
                <option value={TransactionType.TRANSFER}>Transfer</option>
              </select>
            </div>
          </div>

          {(accountFilter || categoryFilter || typeFilter) && (
            <div className="mt-3">
              <button
                onClick={() => {
                  setAccountFilter("");
                  setCategoryFilter("");
                  setTypeFilter("");
                }}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Clear filters
              </button>
            </div>
          )}
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading transactions...</p>
          </div>
        ) : filteredTransactions.length > 0 ? (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Account
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredTransactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(transaction.date)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {transaction.description}
                      </div>
                      {transaction.payee && (
                        <div className="text-sm text-gray-500">{transaction.payee}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getAccountName(transaction.account_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getCategoryName(transaction.category_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={getTransactionTypeColor(transaction.type)}>
                        {getTransactionTypeLabel(transaction.type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                      <span className={getTransactionTypeColor(transaction.type)}>
                        {transaction.type === TransactionType.DEBIT && "-"}
                        {transaction.type === TransactionType.CREDIT && "+"}
                        {formatCurrency(transaction.amount)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() =>
                          router.push(`/dashboard/transactions/${transaction.id}`)
                        }
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(transaction.id)}
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
            <p className="text-gray-600 mb-4">
              {transactions.length === 0
                ? "No transactions yet"
                : "No transactions match your filters"}
            </p>
            {transactions.length === 0 && (
              <button
                onClick={() => router.push("/dashboard/transactions/new")}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                + Add Your First Transaction
              </button>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
