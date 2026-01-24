"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { transactionsAPI, accountsAPI, categoriesAPI, usersAPI } from "@/lib/api";
import { Transaction, Account, Category, TransactionType } from "@/types";
import { formatCurrency, formatDate } from "@/lib/utils/format";
import DashboardLayout from "@/components/layout/DashboardLayout";
import QuickAddBar from "@/components/transactions/QuickAddBar";
import { PayeeIconSmall } from "@/components/payees/PayeeIcon";
import ColumnFilter, { SortOrder } from "@/components/transactions/ColumnFilter";
import ColumnSelector, { ColumnConfig } from "@/components/transactions/ColumnSelector";

export default function TransactionsPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");
  const [hasMore, setHasMore] = useState(true);

  // Filters
  const [accountFilter, setAccountFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [starredFilter, setStarredFilter] = useState<boolean | undefined>(undefined);
  const [payeeFilter, setPayeeFilter] = useState<string>("");
  const [startDateFilter, setStartDateFilter] = useState<string>("");
  const [endDateFilter, setEndDateFilter] = useState<string>("");

  // Sorting
  const [sortBy, setSortBy] = useState<string>("date");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  // Column visibility
  const AVAILABLE_COLUMNS: ColumnConfig[] = [
    { id: "star", label: "⭐ Star", required: false },
    { id: "notes", label: "💬 Notes", required: false },
    { id: "date", label: "Date", required: true },
    { id: "description", label: "Payee / Description", required: false },
    { id: "account", label: "Account", required: false },
    { id: "category", label: "Category", required: false },
    { id: "amount", label: "Amount", required: true },
    { id: "actions", label: "Actions", required: false },
  ];

  const [visibleColumns, setVisibleColumns] = useState<string[]>(
    AVAILABLE_COLUMNS.map((c) => c.id)
  );

  // Pagination
  const PAGE_SIZE = 50;
  const MAX_TRANSACTIONS = 500; // Keep max 500 in memory
  const tableContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
      loadColumnPreferences();
    }
  }, [isAuthenticated]);

  const loadColumnPreferences = async () => {
    try {
      const user = await usersAPI.getMe();
      if (user.ui_preferences?.transactionColumns) {
        setVisibleColumns(user.ui_preferences.transactionColumns);
      }
    } catch (err) {
      console.error("Failed to load column preferences:", err);
    }
  };

  const handleColumnsChange = async (newVisibleColumns: string[]) => {
    setVisibleColumns(newVisibleColumns);

    try {
      await usersAPI.updatePreferences({
        transactionColumns: newVisibleColumns,
      });
    } catch (err) {
      console.error("Failed to save column preferences:", err);
    }
  };

  // Reload when filters or sorting change
  useEffect(() => {
    if (isAuthenticated && !loading) {
      loadData(true);
    }
  }, [accountFilter, categoryFilter, typeFilter, starredFilter, payeeFilter, startDateFilter, endDateFilter, sortBy, sortOrder]);

  const loadData = async (reset: boolean = true) => {
    try {
      // Don't load more if we've hit the max limit
      if (!reset && transactions.length >= MAX_TRANSACTIONS) {
        setHasMore(false);
        return;
      }

      if (reset) {
        setLoading(true);
        setTransactions([]);
        setHasMore(true);
      } else {
        setLoadingMore(true);
      }

      const params = {
        skip: reset ? 0 : transactions.length,
        limit: PAGE_SIZE,
        sort_by: sortBy,
        sort_order: sortOrder || "desc",
        ...(accountFilter && { account_id: parseInt(accountFilter) }),
        ...(categoryFilter && { category_id: parseInt(categoryFilter) }),
        ...(typeFilter && { type: typeFilter }),
        ...(starredFilter !== undefined && { is_starred: starredFilter }),
        ...(payeeFilter && { payee_search: payeeFilter }),
        ...(startDateFilter && { start_date: startDateFilter }),
        ...(endDateFilter && { end_date: endDateFilter }),
      };

      const [txns, accts, cats] = await Promise.all([
        transactionsAPI.getAll(params),
        reset ? accountsAPI.getAll() : Promise.resolve(accounts),
        reset ? categoriesAPI.getAll() : Promise.resolve(categories),
      ]);

      const newTransactions = reset ? txns : [...transactions, ...txns];

      // Enforce MAX_TRANSACTIONS limit
      const limitedTransactions = newTransactions.slice(0, MAX_TRANSACTIONS);
      setTransactions(limitedTransactions);

      if (reset) {
        setAccounts(accts);
        setCategories(cats);
      }

      // Check if there are more transactions available
      const reachedMax = limitedTransactions.length >= MAX_TRANSACTIONS;
      const noMoreData = txns.length < PAGE_SIZE;
      setHasMore(!reachedMax && !noMoreData);

      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load data");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const loadMore = useCallback(() => {
    if (!loadingMore && hasMore && transactions.length < MAX_TRANSACTIONS) {
      loadData(false);
    }
  }, [loadingMore, hasMore, transactions.length]);

  // Infinite scroll detection
  useEffect(() => {
    const handleScroll = () => {
      if (!tableContainerRef.current || loadingMore || !hasMore) return;

      const container = tableContainerRef.current;
      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;

      // Load more when scrolled to within 200px of bottom
      if (scrollHeight - scrollTop - clientHeight < 200) {
        loadMore();
      }
    };

    const container = tableContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [loadMore, loadingMore, hasMore]);

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

  const handleToggleStar = async (id: number) => {
    try {
      const updatedTransaction = await transactionsAPI.toggleStar(id);
      setTransactions(transactions.map((t) =>
        t.id === id ? updatedTransaction : t
      ));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to toggle star");
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
          <div className="flex items-center gap-3">
            <ColumnSelector
              columns={AVAILABLE_COLUMNS}
              visibleColumns={visibleColumns}
              onColumnsChange={handleColumnsChange}
            />
            <button
              onClick={() => router.push("/dashboard/transactions/new")}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              + Add Transaction
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Quick Add Bar */}
        <QuickAddBar onTransactionAdded={loadData} />

        {/* Active Filters Chips */}
        {(accountFilter || categoryFilter || typeFilter || starredFilter !== undefined || payeeFilter || startDateFilter || endDateFilter) && (
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <span className="text-sm text-gray-600">Active filters:</span>

            {starredFilter !== undefined && (
              <button
                onClick={() => setStarredFilter(undefined)}
                className="inline-flex items-center px-3 py-1 text-sm bg-yellow-100 text-yellow-800 rounded-full hover:bg-yellow-200"
              >
                ⭐ Starred
                <span className="ml-2">×</span>
              </button>
            )}

            {payeeFilter && (
              <button
                onClick={() => setPayeeFilter("")}
                className="inline-flex items-center px-3 py-1 text-sm bg-indigo-100 text-indigo-800 rounded-full hover:bg-indigo-200"
              >
                Payee: "{payeeFilter}"
                <span className="ml-2">×</span>
              </button>
            )}

            {(startDateFilter || endDateFilter) && (
              <button
                onClick={() => {
                  setStartDateFilter("");
                  setEndDateFilter("");
                }}
                className="inline-flex items-center px-3 py-1 text-sm bg-teal-100 text-teal-800 rounded-full hover:bg-teal-200"
              >
                Date: {startDateFilter && formatDate(startDateFilter)} - {endDateFilter && formatDate(endDateFilter)}
                <span className="ml-2">×</span>
              </button>
            )}

            {accountFilter && (
              <button
                onClick={() => setAccountFilter("")}
                className="inline-flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200"
              >
                Account: {accounts.find((a) => a.id === parseInt(accountFilter))?.name}
                <span className="ml-2">×</span>
              </button>
            )}

            {categoryFilter && (
              <button
                onClick={() => setCategoryFilter("")}
                className="inline-flex items-center px-3 py-1 text-sm bg-purple-100 text-purple-800 rounded-full hover:bg-purple-200"
              >
                Category: {categories.find((c) => c.id === parseInt(categoryFilter))?.name}
                <span className="ml-2">×</span>
              </button>
            )}

            {typeFilter && (
              <button
                onClick={() => setTypeFilter("")}
                className="inline-flex items-center px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full hover:bg-green-200"
              >
                Type: {typeFilter === TransactionType.DEBIT ? "Expense" : typeFilter === TransactionType.CREDIT ? "Income" : "Transfer"}
                <span className="ml-2">×</span>
              </button>
            )}

            <button
              onClick={() => {
                setAccountFilter("");
                setCategoryFilter("");
                setTypeFilter("");
                setStarredFilter(undefined);
                setPayeeFilter("");
                setStartDateFilter("");
                setEndDateFilter("");
              }}
              className="inline-flex items-center px-3 py-1 text-sm text-red-600 hover:text-red-800"
            >
              Clear all
            </button>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading transactions...</p>
          </div>
        ) : transactions.length > 0 ? (
          <>
            <div className="bg-white shadow sm:rounded-lg overflow-hidden">
              <div
                ref={tableContainerRef}
                className="overflow-x-auto overflow-y-auto"
                style={{ maxHeight: '70vh' }}
              >
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0 z-10">
                    <tr>
                    {visibleColumns.includes("star") && (
                      <th className="px-2 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                        <button
                          onClick={() => setStarredFilter(starredFilter === true ? undefined : true)}
                          className={`text-xl hover:scale-110 transition-transform ${
                            starredFilter === true ? "opacity-100" : "opacity-50"
                          }`}
                          title="Filter starred"
                        >
                          ⭐
                        </button>
                      </th>
                    )}
                    {visibleColumns.includes("notes") && (
                      <th className="px-2 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                        💬
                      </th>
                    )}
                    {visibleColumns.includes("date") && (
                      <ColumnFilter
                        label="Date"
                        sortable
                        filterable
                        filterType="dateRange"
                        currentSort={sortBy === "date" ? sortOrder : null}
                        currentDateRange={{ start: startDateFilter, end: endDateFilter }}
                        onSort={(order) => {
                          setSortBy("date");
                          setSortOrder(order);
                        }}
                        onDateRangeFilter={(start, end) => {
                          setStartDateFilter(start || "");
                          setEndDateFilter(end || "");
                        }}
                      />
                    )}
                    {visibleColumns.includes("description") && (
                      <ColumnFilter
                        label="Payee"
                        filterable
                        filterType="text"
                        currentFilter={payeeFilter}
                        onFilter={(value) => setPayeeFilter(value?.toString() || "")}
                      />
                    )}
                    {visibleColumns.includes("account") && (
                      <ColumnFilter
                        label="Account"
                        filterable
                        filterOptions={accounts.map((a) => ({ label: a.name, value: a.id.toString() }))}
                        currentFilter={accountFilter}
                        onFilter={(value) => setAccountFilter(value?.toString() || "")}
                      />
                    )}
                    {visibleColumns.includes("category") && (
                      <ColumnFilter
                        label="Category"
                        filterable
                        filterOptions={categories.map((c) => ({ label: c.name, value: c.id.toString() }))}
                        currentFilter={categoryFilter}
                        onFilter={(value) => setCategoryFilter(value?.toString() || "")}
                      />
                    )}
                    {visibleColumns.includes("amount") && (
                      <ColumnFilter
                        label="Amount"
                        sortable
                        filterable
                        align="right"
                        currentSort={sortBy === "amount" ? sortOrder : null}
                        onSort={(order) => {
                          setSortBy("amount");
                          setSortOrder(order);
                        }}
                        filterOptions={[
                          { label: "📤 Expense", value: TransactionType.DEBIT },
                          { label: "📥 Income", value: TransactionType.CREDIT },
                          { label: "🔄 Transfer", value: TransactionType.TRANSFER },
                        ]}
                        currentFilter={typeFilter}
                        onFilter={(value) => setTypeFilter(value?.toString() || "")}
                      />
                    )}
                    {visibleColumns.includes("actions") && (
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((transaction) => (
                    <tr key={transaction.id} className={`hover:bg-gray-50 ${transaction.is_starred ? 'bg-yellow-50' : ''}`}>
                      {visibleColumns.includes("star") && (
                        <td className="px-2 py-4 text-center">
                          <button
                            onClick={() => handleToggleStar(transaction.id)}
                            className="text-2xl hover:scale-110 transition-transform"
                            title={transaction.is_starred ? "Unstar" : "Star"}
                          >
                            {transaction.is_starred ? "⭐" : "☆"}
                          </button>
                        </td>
                      )}
                      {visibleColumns.includes("notes") && (
                        <td className="px-2 py-4 text-center">
                          {transaction.notes && (
                            <div
                              className="inline-block text-xl cursor-help"
                              title={transaction.notes}
                            >
                              💬
                            </div>
                          )}
                        </td>
                      )}
                      {visibleColumns.includes("date") && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(transaction.date)}
                        </td>
                      )}
                      {visibleColumns.includes("description") && (
                        <td className="px-6 py-4">
                          {transaction.payee_name ? (
                            <>
                              <div className="flex items-center gap-2">
                                <PayeeIconSmall
                                  logoUrl={transaction.payee_logo_url}
                                  name={transaction.payee_name}
                                />
                                <span className="text-sm font-medium text-gray-900">{transaction.payee_name}</span>
                              </div>
                              <div className="text-xs text-gray-500 mt-1 truncate">
                                {transaction.description}
                              </div>
                            </>
                          ) : (
                            <div className="text-sm font-medium text-gray-900">
                              {transaction.description}
                            </div>
                          )}
                        </td>
                      )}
                      {visibleColumns.includes("account") && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getAccountName(transaction.account_id)}
                        </td>
                      )}
                      {visibleColumns.includes("category") && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getCategoryName(transaction.category_id)}
                        </td>
                      )}
                      {visibleColumns.includes("amount") && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                          <span className={getTransactionTypeColor(transaction.type)}>
                            {transaction.type === TransactionType.DEBIT && "-"}
                            {transaction.type === TransactionType.CREDIT && "+"}
                            {formatCurrency(transaction.amount)}
                          </span>
                        </td>
                      )}
                      {visibleColumns.includes("actions") && (
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
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Inline Loading Indicator for Infinite Scroll */}
              {loadingMore && (
                <div className="flex items-center justify-center py-4 border-t">
                  <svg
                    className="animate-spin h-5 w-5 text-blue-600 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span className="text-sm text-gray-600">Loading more transactions...</span>
                </div>
              )}

              {/* End of list indicator */}
              {!hasMore && transactions.length >= PAGE_SIZE && (
                <div className="text-center py-4 border-t">
                  <p className="text-sm text-gray-500">
                    All {transactions.length} transactions loaded
                  </p>
                </div>
              )}

              {/* Max limit reached indicator */}
              {transactions.length >= MAX_TRANSACTIONS && hasMore && (
                <div className="text-center py-4 border-t bg-yellow-50">
                  <p className="text-sm text-gray-700">
                    Showing first {MAX_TRANSACTIONS} transactions. Use filters to narrow results.
                  </p>
                </div>
              )}
              </div>
            </div>

            {/* Transaction count */}
            <div className="mt-3 text-center">
              <p className="text-sm text-gray-500">
                Showing {transactions.length} transaction{transactions.length !== 1 ? 's' : ''}
              </p>
            </div>
          </>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-600 mb-4">No transactions yet</p>
            <button
              onClick={() => router.push("/dashboard/transactions/new")}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              + Add Your First Transaction
            </button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
