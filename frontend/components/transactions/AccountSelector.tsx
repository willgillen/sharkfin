"use client";

import { Account } from "@/types";
import { formatCurrency } from "@/lib/utils/format";

interface AccountSelectorProps {
  accounts: Account[];
  selectedAccountId: number | null;
  onAccountChange: (accountId: number) => void;
  loading?: boolean;
}

export default function AccountSelector({
  accounts,
  selectedAccountId,
  onAccountChange,
  loading = false,
}: AccountSelectorProps) {
  const selectedAccount = accounts.find((a) => a.id === selectedAccountId);

  if (loading || accounts.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-4 mb-6">
        <div className="animate-pulse flex items-center gap-4">
          <div className="h-10 bg-surface-secondary rounded w-48"></div>
          <div className="h-6 bg-surface-secondary rounded w-32"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-lg p-4 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <div className="flex items-center gap-3">
          <label htmlFor="account-selector" className="text-sm font-medium text-text-secondary whitespace-nowrap">
            Viewing:
          </label>
          <select
            id="account-selector"
            value={selectedAccountId || ""}
            onChange={(e) => onAccountChange(parseInt(e.target.value))}
            className="block w-full sm:w-auto min-w-[200px] px-4 py-2 text-base font-medium
                     border border-border rounded-lg bg-surface text-text-primary
                     focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                     appearance-none cursor-pointer"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
              backgroundPosition: "right 0.5rem center",
              backgroundRepeat: "no-repeat",
              backgroundSize: "1.5em 1.5em",
              paddingRight: "2.5rem",
            }}
          >
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </div>

        {selectedAccount && (
          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-text-tertiary">Current Balance: </span>
              <span className={`font-semibold ${
                parseFloat(selectedAccount.current_balance) >= 0
                  ? "text-success-600"
                  : "text-danger-600"
              }`}>
                {formatCurrency(selectedAccount.current_balance)}
              </span>
            </div>
            <div className="hidden sm:block">
              <span className="text-text-tertiary">Type: </span>
              <span className="text-text-primary capitalize">
                {selectedAccount.type.replace("_", " ")}
              </span>
            </div>
            {selectedAccount.institution && (
              <div className="hidden md:block">
                <span className="text-text-tertiary">Institution: </span>
                <span className="text-text-primary">{selectedAccount.institution}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
