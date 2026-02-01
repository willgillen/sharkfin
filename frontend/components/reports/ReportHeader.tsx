"use client";

import { ReactNode } from "react";
import DateRangePicker, { DateRange } from "./DateRangePicker";
import AccountFilter from "./AccountFilter";
import { Account } from "@/types";

interface ReportHeaderProps {
  title: string;
  description?: string;
  dateRange: DateRange;
  onDateRangeChange: (range: DateRange) => void;
  accounts?: Account[];
  selectedAccountId?: number | null;
  onAccountChange?: (accountId: number | null) => void;
  accountsLoading?: boolean;
  showAccountFilter?: boolean;
  actions?: ReactNode;
}

export default function ReportHeader({
  title,
  description,
  dateRange,
  onDateRangeChange,
  accounts = [],
  selectedAccountId = null,
  onAccountChange,
  accountsLoading = false,
  showAccountFilter = true,
  actions,
}: ReportHeaderProps) {
  return (
    <div className="mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{title}</h1>
          {description && (
            <p className="mt-1 text-sm text-text-secondary">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <DateRangePicker value={dateRange} onChange={onDateRangeChange} />

        {showAccountFilter && onAccountChange && (
          <AccountFilter
            accounts={accounts}
            selectedAccountId={selectedAccountId}
            onChange={onAccountChange}
            loading={accountsLoading}
          />
        )}
      </div>
    </div>
  );
}
