"use client";

import { useRef, useCallback } from "react";
import { VariableSizeList as List } from "react-window";
import InfiniteLoader from "react-window-infinite-loader";
import { Transaction, Account, Category, TransactionType } from "@/types";
import { formatCurrency, formatDate } from "@/lib/utils/format";
import { PayeeIconSmall } from "@/components/payees/PayeeIcon";

interface VirtualizedTransactionTableProps {
  transactions: Transaction[];
  accounts: Account[];
  categories: Category[];
  visibleColumns: string[];
  hasMore: boolean;
  isLoadingMore: boolean;
  onLoadMore: () => void;
  onToggleStar: (id: number) => void;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
}

export default function VirtualizedTransactionTable({
  transactions,
  accounts,
  categories,
  visibleColumns,
  hasMore,
  isLoadingMore,
  onLoadMore,
  onToggleStar,
  onEdit,
  onDelete,
}: VirtualizedTransactionTableProps) {
  const listRef = useRef<List>(null);

  const getAccountName = (accountId: number): string => {
    return accounts.find((a) => a.id === accountId)?.name || "Unknown";
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

  // Calculate item count (transactions + 1 for loading indicator if hasMore)
  const itemCount = hasMore ? transactions.length + 1 : transactions.length;

  // Check if item is loaded
  const isItemLoaded = (index: number) => !hasMore || index < transactions.length;

  // Load more items
  const loadMoreItems = isLoadingMore ? () => {} : onLoadMore;

  // Get item size (row height)
  const getItemSize = (index: number) => {
    if (!isItemLoaded(index)) {
      return 60; // Loading row
    }
    const transaction = transactions[index];
    // Base height + extra for payee if present
    return transaction.payee_name ? 72 : 56;
  };

  // Render row
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    if (!isItemLoaded(index)) {
      return (
        <div style={style} className="flex items-center justify-center py-4 border-b">
          <div className="flex items-center gap-2 text-text-secondary">
            <svg
              className="animate-spin h-5 w-5"
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
            <span className="text-sm">Loading more transactions...</span>
          </div>
        </div>
      );
    }

    const transaction = transactions[index];

    return (
      <div
        style={style}
        className={`flex items-center border-b hover:bg-surface-secondary ${
          transaction.is_starred ? "bg-warning-50" : ""
        }`}
      >
        <div className="flex-1 flex items-center min-w-0">
          {visibleColumns.includes("star") && (
            <div className="px-2 py-4 w-12 flex-shrink-0 text-center">
              <button
                onClick={() => onToggleStar(transaction.id)}
                className="text-2xl hover:scale-110 transition-transform"
                title={transaction.is_starred ? "Unstar" : "Star"}
              >
                {transaction.is_starred ? "⭐" : "☆"}
              </button>
            </div>
          )}

          {visibleColumns.includes("notes") && (
            <div className="px-2 py-4 w-12 flex-shrink-0 text-center">
              {transaction.notes && (
                <div
                  className="inline-block text-xl cursor-help"
                  title={transaction.notes}
                >
                  💬
                </div>
              )}
            </div>
          )}

          {visibleColumns.includes("date") && (
            <div className="px-6 py-4 w-32 flex-shrink-0 whitespace-nowrap text-sm text-text-primary">
              {formatDate(transaction.date)}
            </div>
          )}

          {visibleColumns.includes("description") && (
            <div className="px-6 py-4 flex-1 min-w-0">
              <div className="text-sm font-medium text-text-primary truncate">
                {transaction.description}
              </div>
              {transaction.payee_name && (
                <div className="flex items-center gap-2 mt-1">
                  <PayeeIconSmall
                    logoUrl={transaction.payee_logo_url}
                    name={transaction.payee_name}
                  />
                  <span className="text-sm text-text-tertiary truncate">
                    {transaction.payee_name}
                  </span>
                </div>
              )}
            </div>
          )}

          {visibleColumns.includes("account") && (
            <div className="px-6 py-4 w-40 flex-shrink-0 whitespace-nowrap text-sm text-text-tertiary truncate">
              {getAccountName(transaction.account_id)}
            </div>
          )}

          {visibleColumns.includes("category") && (
            <div className="px-6 py-4 w-40 flex-shrink-0 whitespace-nowrap text-sm text-text-tertiary truncate">
              {getCategoryName(transaction.category_id)}
            </div>
          )}

          {visibleColumns.includes("amount") && (
            <div className="px-6 py-4 w-32 flex-shrink-0 whitespace-nowrap text-sm text-right font-medium">
              <span className={getTransactionTypeColor(transaction.type)}>
                {transaction.type === TransactionType.DEBIT && "-"}
                {transaction.type === TransactionType.CREDIT && "+"}
                {formatCurrency(transaction.amount)}
              </span>
            </div>
          )}

          {visibleColumns.includes("actions") && (
            <div className="px-6 py-4 w-40 flex-shrink-0 whitespace-nowrap text-right text-sm font-medium">
              <button
                onClick={() => onEdit(transaction.id)}
                className="text-primary-600 hover:text-primary-900 mr-4"
              >
                Edit
              </button>
              <button
                onClick={() => onDelete(transaction.id)}
                className="text-danger-600 hover:text-danger-900"
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-surface shadow overflow-hidden sm:rounded-lg">
      <InfiniteLoader
        isItemLoaded={isItemLoaded}
        itemCount={itemCount}
        loadMoreItems={loadMoreItems}
        threshold={5}
      >
        {({ onItemsRendered, ref }) => (
          <List
            ref={(list) => {
              ref(list);
              (listRef as any).current = list;
            }}
            height={600}
            itemCount={itemCount}
            itemSize={getItemSize}
            onItemsRendered={onItemsRendered}
            width="100%"
            className="divide-y divide-border-light"
          >
            {Row}
          </List>
        )}
      </InfiniteLoader>
    </div>
  );
}
