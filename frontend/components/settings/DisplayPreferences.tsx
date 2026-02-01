"use client";

import SettingItem from "./SettingItem";
import { UserPreferences, PreferencesMetadata } from "@/types";

interface DisplayPreferencesProps {
  preferences: UserPreferences;
  metadata: PreferencesMetadata;
  saving: Record<string, boolean>;
  onUpdate: (key: keyof UserPreferences, value: any) => Promise<void>;
  onReset: (key: string) => Promise<void>;
  isModified: (key: string) => boolean;
}

export default function DisplayPreferences({
  preferences,
  metadata,
  saving,
  onUpdate,
  onReset,
  isModified,
}: DisplayPreferencesProps) {
  const dateFormatOptions = [
    { value: "MM/DD/YYYY", label: "MM/DD/YYYY (01/31/2026)" },
    { value: "DD/MM/YYYY", label: "DD/MM/YYYY (31/01/2026)" },
    { value: "YYYY-MM-DD", label: "YYYY-MM-DD (2026-01-31)" },
    { value: "MMM D, YYYY", label: "MMM D, YYYY (Jan 31, 2026)" },
  ];

  const numberFormatOptions = [
    { value: "1,234.56", label: "1,234.56 (US/UK)" },
    { value: "1.234,56", label: "1.234,56 (EU)" },
    { value: "1 234.56", label: "1 234.56 (Space separator)" },
  ];

  const currencyPositionOptions = [
    { value: "before", label: "Before amount ($100)" },
    { value: "after", label: "After amount (100$)" },
  ];

  const weekDayOptions = [
    { value: "sunday", label: "Sunday" },
    { value: "monday", label: "Monday" },
  ];

  return (
    <div className="divide-y divide-border">
      <SettingItem
        type="select"
        label="Date Format"
        description="How dates are displayed throughout the application."
        value={preferences.date_format || "MM/DD/YYYY"}
        options={dateFormatOptions}
        onChange={(value) => onUpdate("date_format", value)}
        saving={saving.date_format}
        isModified={isModified("date_format")}
        onReset={() => onReset("date_format")}
      />

      <SettingItem
        type="select"
        label="Number Format"
        description="How numbers and currency amounts are formatted."
        value={preferences.number_format || "1,234.56"}
        options={numberFormatOptions}
        onChange={(value) => onUpdate("number_format", value)}
        saving={saving.number_format}
        isModified={isModified("number_format")}
        onReset={() => onReset("number_format")}
      />

      <SettingItem
        type="string"
        label="Currency Symbol"
        description="Symbol to display with amounts (e.g., $, €, £)."
        value={preferences.currency_symbol || "$"}
        placeholder="$"
        onChange={(value) => onUpdate("currency_symbol", value)}
        saving={saving.currency_symbol}
        isModified={isModified("currency_symbol")}
        onReset={() => onReset("currency_symbol")}
      />

      <SettingItem
        type="select"
        label="Currency Position"
        description="Where to display the currency symbol."
        value={preferences.currency_position || "before"}
        options={currencyPositionOptions}
        onChange={(value) => onUpdate("currency_position", value)}
        saving={saving.currency_position}
        isModified={isModified("currency_position")}
        onReset={() => onReset("currency_position")}
      />

      <SettingItem
        type="number"
        label="Decimal Places"
        description="Number of decimal places for currency amounts."
        value={preferences.currency_decimals ?? 2}
        min={0}
        max={4}
        onChange={(value) => onUpdate("currency_decimals", value)}
        saving={saving.currency_decimals}
        isModified={isModified("currency_decimals")}
        onReset={() => onReset("currency_decimals")}
      />

      <SettingItem
        type="select"
        label="Start of Week"
        description="First day of the week for calendars and reports."
        value={preferences.start_of_week || "sunday"}
        options={weekDayOptions}
        onChange={(value) => onUpdate("start_of_week", value)}
        saving={saving.start_of_week}
        isModified={isModified("start_of_week")}
        onReset={() => onReset("start_of_week")}
      />
    </div>
  );
}
