"use client";

import SettingItem from "./SettingItem";
import { UserPreferences, PreferencesMetadata } from "@/types";

interface TransactionPreferencesProps {
  preferences: UserPreferences;
  metadata: PreferencesMetadata;
  saving: Record<string, boolean>;
  onUpdate: (key: keyof UserPreferences, value: any) => Promise<void>;
  onReset: (key: string) => Promise<void>;
  isModified: (key: string) => boolean;
}

export default function TransactionPreferences({
  preferences,
  metadata,
  saving,
  onUpdate,
  onReset,
  isModified,
}: TransactionPreferencesProps) {
  const rowsPerPageOptions = [
    { value: 25, label: "25 rows" },
    { value: 50, label: "50 rows" },
    { value: 100, label: "100 rows" },
  ];

  const sortColumnOptions = [
    { value: "date", label: "Date" },
    { value: "payee", label: "Payee" },
    { value: "amount", label: "Amount" },
    { value: "category", label: "Category" },
  ];

  const sortOrderOptions = [
    { value: "desc", label: "Newest first" },
    { value: "asc", label: "Oldest first" },
  ];

  return (
    <div className="divide-y divide-border">
      <SettingItem
        type="select"
        label="Rows Per Page"
        description="Number of transactions to display per page."
        value={preferences.transactions_rows_per_page || 50}
        options={rowsPerPageOptions}
        onChange={(value) => onUpdate("transactions_rows_per_page", value)}
        saving={saving.transactions_rows_per_page}
        isModified={isModified("transactions_rows_per_page")}
        onReset={() => onReset("transactions_rows_per_page")}
      />

      <SettingItem
        type="select"
        label="Default Sort Column"
        description="Which column to sort transactions by default."
        value={preferences.transactions_sort_column || "date"}
        options={sortColumnOptions}
        onChange={(value) => onUpdate("transactions_sort_column", value)}
        saving={saving.transactions_sort_column}
        isModified={isModified("transactions_sort_column")}
        onReset={() => onReset("transactions_sort_column")}
      />

      <SettingItem
        type="select"
        label="Default Sort Order"
        description="Sort direction for transactions."
        value={preferences.transactions_sort_order || "desc"}
        options={sortOrderOptions}
        onChange={(value) => onUpdate("transactions_sort_order", value)}
        saving={saving.transactions_sort_order}
        isModified={isModified("transactions_sort_order")}
        onReset={() => onReset("transactions_sort_order")}
      />
    </div>
  );
}
