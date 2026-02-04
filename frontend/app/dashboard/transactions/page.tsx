"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { transactionsAPI, accountsAPI, categoriesAPI, usersAPI, reportsAPI } from "@/lib/api";
import { Transaction, Account, Category, TransactionType } from "@/types";
import { formatCurrency, formatDate } from "@/lib/utils/format";
import DashboardLayout from "@/components/layout/DashboardLayout";
import QuickAddBar from "@/components/transactions/QuickAddBar";
import { PayeeIconSmall } from "@/components/payees/PayeeIcon";
import ColumnFilter, { SortOrder } from "@/components/transactions/ColumnFilter";
import ColumnSelector, { ColumnConfig } from "@/components/transactions/ColumnSelector";
import AccountSelector from "@/components/transactions/AccountSelector";

export default function TransactionsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");
  const [hasMore, setHasMore] = useState(true);
  const [exporting, setExporting] = useState(false);

  // Selected account (required - always viewing one account)
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);

  // Other filters
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [starredFilter, setStarredFilter] = useState<boolean | undefined>(undefined);
  const [payeeFilter, setPayeeFilter] = useState<string>("");
  const [startDateFilter, setStartDateFilter] = useState<string>("");
  const [endDateFilter, setEndDateFilter] = useState<string>("");

  // Sorting
  const [sortBy, setSortBy] = useState<string>("date");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  // Column visibility - account column hidden by default since we always view one account
  const AVAILABLE_COLUMNS: ColumnConfig[] = [
    { id: "star", label: "⭐ Star", required: false },
    { id: "notes", label: "💬 Notes", required: false },
    { id: "date", label: "Date", required: true },
    { id: "description", label: "Payee / Description", required: false },
    { id: "category", label: "Category", required: false },
    { id: "amount", label: "Amount", required: true },
    { id: "balance", label: "Balance", required: false },
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

  // Load accounts first, then set selected account from URL or default to first
  useEffect(() => {
    if (isAuthenticated) {
      loadAccounts();
      loadColumnPreferences();
      // Initialize filters from URL params
      initFiltersFromUrl();
    }
  }, [isAuthenticated]);

  // Initialize filters from URL parameters (for drill-down from reports)
  const initFiltersFromUrl = () => {
    const urlCategoryId = searchParams.get("category_id");
    const urlStartDate = searchParams.get("start_date");
    const urlEndDate = searchParams.get("end_date");
    const urlType = searchParams.get("type");

    if (urlCategoryId) {
      setCategoryFilter(urlCategoryId);
    }
    if (urlStartDate) {
      setStartDateFilter(urlStartDate);
    }
    if (urlEndDate) {
      setEndDateFilter(urlEndDate);
    }
    if (urlType) {
      setTypeFilter(urlType);
    }
  };

  const loadAccounts = async () => {
    try {
      setAccountsLoading(true);
      const [accts, cats] = await Promise.all([
        accountsAPI.getAll(),
        categoriesAPI.getAll(),
      ]);
      setAccounts(accts);
      setCategories(cats);

      // Get account from URL or default to first account
      const urlAccountId = searchParams.get("account");
      if (urlAccountId && accts.some((a) => a.id === parseInt(urlAccountId))) {
        setSelectedAccountId(parseInt(urlAccountId));
      } else if (accts.length > 0) {
        setSelectedAccountId(accts[0].id);
        // Update URL with default account
        router.replace(`/dashboard/transactions?account=${accts[0].id}`, { scroll: false });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load accounts");
    } finally {
      setAccountsLoading(false);
    }
  };

  // Load transactions when selected account changes
  useEffect(() => {
    if (isAuthenticated && selectedAccountId !== null) {
      loadTransactions(true);
    }
  }, [selectedAccountId]);

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

  // Reload when filters or sorting change (but not when account changes - that's handled separately)
  useEffect(() => {
    if (isAuthenticated && selectedAccountId !== null && !accountsLoading) {
      loadTransactions(true);
    }
  }, [categoryFilter, typeFilter, starredFilter, payeeFilter, startDateFilter, endDateFilter, sortBy, sortOrder]);

  const loadTransactions = async (reset: boolean = true) => {
    // Don't load if no account is selected
    if (selectedAccountId === null) return;

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
        account_id: selectedAccountId, // Always filter by selected account
        ...(categoryFilter && { category_id: parseInt(categoryFilter) }),
        ...(typeFilter && { type: typeFilter }),
        ...(starredFilter !== undefined && { is_starred: starredFilter }),
        ...(payeeFilter && { payee_search: payeeFilter }),
        ...(startDateFilter && { start_date: startDateFilter }),
        ...(endDateFilter && { end_date: endDateFilter }),
      };

      const txns = await transactionsAPI.getAll(params);
      const newTransactions = reset ? txns : [...transactions, ...txns];

      // Enforce MAX_TRANSACTIONS limit
      const limitedTransactions = newTransactions.slice(0, MAX_TRANSACTIONS);
      setTransactions(limitedTransactions);

      // Check if there are more transactions available
      const reachedMax = limitedTransactions.length >= MAX_TRANSACTIONS;
      const noMoreData = txns.length < PAGE_SIZE;
      setHasMore(!reachedMax && !noMoreData);

      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load transactions");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  // Keep old function name for compatibility with QuickAddBar
  const loadData = (reset: boolean = true) => loadTransactions(reset);

  const loadMore = useCallback(() => {
    if (!loadingMore && hasMore && transactions.length < MAX_TRANSACTIONS) {
      loadTransactions(false);
    }
  }, [loadingMore, hasMore, transactions.length, selectedAccountId]);

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

  const handleAccountChange = (accountId: number) => {
    setSelectedAccountId(accountId);
    // Update URL with new account
    router.replace(`/dashboard/transactions?account=${accountId}`, { scroll: false });
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

  const getCategoryName = (categoryId: number | null): string => {
    if (!categoryId) return "Uncategorized";
    return categories.find((c) => c.id === categoryId)?.name || "Unknown";
  };

  const getTransactionTypeColor = (type: TransactionType): string => {
    const colors: Record<TransactionType, string> = {
      [TransactionType.DEBIT]: "text-danger-600",
      [TransactionType.CREDIT]: "text-success-600",
      [TransactionType.TRANSFER]: "text-primary-600",
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

  const handleExportCSV = async () => {
    if (!selectedAccountId) return;

    setExporting(true);
    try {
      await reportsAPI.exportTransactions({
        startDate: startDateFilter || undefined,
        endDate: endDateFilter || undefined,
        accountId: selectedAccountId,
        categoryId: categoryFilter ? parseInt(categoryFilter) : undefined,
        type: typeFilter || undefined,
        payeeSearch: payeeFilter || undefined,
      });
    } catch (err: any) {
      setError("Failed to export transactions");
    } finally {
      setExporting(false);
    }
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
          <h1 className="text-3xl font-bold text-text-primary">Transactions</h1>
          <div className="flex items-center gap-3">
            <ColumnSelector
              columns={AVAILABLE_COLUMNS}
              visibleColumns={visibleColumns}
              onColumnsChange={handleColumnsChange}
            />
            <button
              onClick={handleExportCSV}
              disabled={!selectedAccountId || exporting}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-primary bg-surface border border-border rounded-md hover:bg-surface-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {exporting ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Exporting...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export CSV
                </>
              )}
            </button>
            <button
              onClick={() => router.push("/dashboard/transactions/new")}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              + Add Transaction
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-danger-50 p-4">
            <p className="text-sm text-danger-800">{error}</p>
          </div>
        )}

        {/* Account Selector - Always visible */}
        <AccountSelector
          accounts={accounts}
          selectedAccountId={selectedAccountId}
          onAccountChange={handleAccountChange}
          loading={accountsLoading}
        />

        {/* Quick Add Bar - only show when account is selected */}
        {selectedAccountId && (
          <QuickAddBar accountId={selectedAccountId} onTransactionAdded={loadData} />
        )}

        {/* Active Filters Chips */}
        {(categoryFilter || typeFilter || starredFilter !== undefined || payeeFilter || startDateFilter || endDateFilter) && (
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <span className="text-sm text-text-secondary">Active filters:</span>

            {starredFilter !== undefined && (
              <button
                onClick={() => setStarredFilter(undefined)}
                className="inline-flex items-center px-3 py-1 text-sm bg-warning-100 text-warning-800 rounded-full hover:bg-warning-200"
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
                className="inline-flex items-center px-3 py-1 text-sm bg-success-100 text-success-800 rounded-full hover:bg-success-200"
              >
                Type: {typeFilter === TransactionType.DEBIT ? "Expense" : typeFilter === TransactionType.CREDIT ? "Income" : "Transfer"}
                <span className="ml-2">×</span>
              </button>
            )}

            <button
              onClick={() => {
                setCategoryFilter("");
                setTypeFilter("");
                setStarredFilter(undefined);
                setPayeeFilter("");
                setStartDateFilter("");
                setEndDateFilter("");
              }}
              className="inline-flex items-center px-3 py-1 text-sm text-danger-600 hover:text-danger-800"
            >
              Clear all
            </button>
          </div>
        )}

        {accountsLoading || loading ? (
          <div className="text-center py-12">
            <p className="text-text-secondary">Loading transactions...</p>
          </div>
        ) : accounts.length === 0 ? (
          <div className="text-center py-12 bg-surface rounded-lg shadow">
            <p className="text-text-secondary mb-4">No accounts found. Create an account to start tracking transactions.</p>
            <button
              onClick={() => router.push("/dashboard/accounts/new")}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              + Create Account
            </button>
          </div>
        ) : transactions.length > 0 ? (
          <>
            <div className="bg-surface shadow sm:rounded-lg">
              <div
                ref={tableContainerRef}
                className="overflow-x-auto overflow-y-auto"
                style={{ maxHeight: '70vh' }}
              >
                <table className="w-full divide-y divide-border">
                  <thead className="bg-surface-secondary sticky top-0 z-20">
                    <tr>
                    {visibleColumns.includes("star") && (
                      <th className="px-2 py-3 text-center text-xs font-medium text-text-tertiary uppercase tracking-wider w-12">
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
                      <th className="px-2 py-3 text-center text-xs font-medium text-text-tertiary uppercase tracking-wider w-12">
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
                        width="20rem"
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
                    {visibleColumns.includes("balance") && (
                      <th
                        className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider"
                        title={
                          sortBy !== "date"
                            ? "Sort by date to see running balance"
                            : "Running balance after each transaction"
                        }
                      >
                        Balance
                        {sortBy !== "date" && (
                          <span className="ml-1 text-warning-500" title="Sort by date to see running balance">
                            ⚠
                          </span>
                        )}
                      </th>
                    )}
                    {visibleColumns.includes("actions") && (
                      <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                        Actions
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-surface divide-y divide-border">
                  {transactions.map((transaction) => (
                    <tr key={transaction.id} className={`hover:bg-surface-secondary ${transaction.is_starred ? 'bg-warning-50' : ''}`}>
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
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary">
                          {formatDate(transaction.date)}
                        </td>
                      )}
                      {visibleColumns.includes("description") && (
                        <td className="px-6 py-4" style={{ maxWidth: "20rem" }}>
                          {transaction.payee_name ? (
                            <>
                              <div className="flex items-center gap-2 min-w-0">
                                <PayeeIconSmall
                                  logoUrl={transaction.payee_logo_url}
                                  name={transaction.payee_name}
                                />
                                <span className="text-sm font-medium text-text-primary truncate">{transaction.payee_name}</span>
                              </div>
                              <div className="text-xs text-text-tertiary mt-1 truncate">
                                {transaction.description}
                              </div>
                            </>
                          ) : (
                            <div className="text-sm font-medium text-text-primary truncate">
                              {transaction.description}
                            </div>
                          )}
                        </td>
                      )}
                      {visibleColumns.includes("category") && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-text-tertiary">
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
                      {visibleColumns.includes("balance") && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                          {transaction.running_balance !== null && transaction.running_balance !== undefined ? (
                            <span className="text-text-primary">
                              {formatCurrency(transaction.running_balance)}
                            </span>
                          ) : (
                            <span
                              className="text-text-disabled cursor-help"
                              title={
                                sortBy !== "date"
                                  ? "Sort by date to see running balance"
                                  : "Balance not available"
                              }
                            >
                              —
                            </span>
                          )}
                        </td>
                      )}
                      {visibleColumns.includes("actions") && (
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() =>
                              router.push(`/dashboard/transactions/${transaction.id}`)
                            }
                            className="text-primary-600 hover:text-primary-900 mr-4"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(transaction.id)}
                            className="text-danger-600 hover:text-danger-900"
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
                <div className="flex items-center justify-center py-4 border-t border-border-light">
                  <svg
                    className="animate-spin h-5 w-5 text-primary-600 mr-2"
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
                  <span className="text-sm text-text-secondary">Loading more transactions...</span>
                </div>
              )}

              {/* End of list indicator */}
              {!hasMore && transactions.length >= PAGE_SIZE && (
                <div className="text-center py-4 border-t border-border-light">
                  <p className="text-sm text-text-tertiary">
                    All {transactions.length} transactions loaded
                  </p>
                </div>
              )}

              {/* Max limit reached indicator */}
              {transactions.length >= MAX_TRANSACTIONS && hasMore && (
                <div className="text-center py-4 border-t border-border-light bg-warning-50">
                  <p className="text-sm text-text-secondary">
                    Showing first {MAX_TRANSACTIONS} transactions. Use filters to narrow results.
                  </p>
                </div>
              )}
              </div>
            </div>

            {/* Transaction count */}
            <div className="mt-3 text-center">
              <p className="text-sm text-text-tertiary">
                Showing {transactions.length} transaction{transactions.length !== 1 ? 's' : ''}
              </p>
            </div>
          </>
        ) : (
          <div className="text-center py-12 bg-surface rounded-lg shadow">
            <p className="text-text-secondary mb-4">No transactions yet</p>
            <button
              onClick={() => router.push("/dashboard/transactions/new")}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              + Add Your First Transaction
            </button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
