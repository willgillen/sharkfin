"use client";

import { Account } from "@/types";

interface AccountFilterProps {
  accounts: Account[];
  selectedAccountId: number | null; // null means "All Accounts"
  onChange: (accountId: number | null) => void;
  loading?: boolean;
}

export default function AccountFilter({
  accounts,
  selectedAccountId,
  onChange,
  loading = false,
}: AccountFilterProps) {
  if (loading) {
    return (
      <div className="animate-pulse h-10 bg-surface-secondary rounded-lg w-48"></div>
    );
  }

  return (
    <div className="relative">
      <select
        value={selectedAccountId ?? "all"}
        onChange={(e) => onChange(e.target.value === "all" ? null : parseInt(e.target.value))}
        className="appearance-none px-4 py-2 pr-10 border border-border rounded-lg bg-surface text-text-primary font-medium cursor-pointer hover:bg-surface-secondary transition-colors focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
          backgroundPosition: "right 0.5rem center",
          backgroundRepeat: "no-repeat",
          backgroundSize: "1.5em 1.5em",
        }}
      >
        <option value="all">All Accounts</option>
        {accounts.map((account) => (
          <option key={account.id} value={account.id}>
            {account.name}
          </option>
        ))}
      </select>
    </div>
  );
}
