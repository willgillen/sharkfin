"use client";

import { useState, useEffect } from "react";
import SettingItem from "./SettingItem";
import { UserPreferences, PreferencesMetadata, Account } from "@/types";
import { accountsAPI } from "@/lib/api";

interface ImportPreferencesProps {
  preferences: UserPreferences;
  metadata: PreferencesMetadata;
  saving: Record<string, boolean>;
  onUpdate: (key: keyof UserPreferences, value: any) => Promise<void>;
  onReset: (key: string) => Promise<void>;
  isModified: (key: string) => boolean;
}

export default function ImportPreferences({
  preferences,
  metadata,
  saving,
  onUpdate,
  onReset,
  isModified,
}: ImportPreferencesProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const data = await accountsAPI.getAll();
      setAccounts(data);
    } catch (err) {
      console.error("Failed to load accounts:", err);
    }
  };

  const accountOptions = [
    { value: 0, label: "Ask each time" },
    ...accounts.map((account) => ({
      value: account.id,
      label: account.name,
    })),
  ];

  const duplicateStrictnessOptions = [
    { value: "strict", label: "Strict (exact match required)" },
    { value: "moderate", label: "Moderate (recommended)" },
    { value: "relaxed", label: "Relaxed (date + amount only)" },
  ];

  return (
    <div className="divide-y divide-border">
      <SettingItem
        type="select"
        label="Default Import Account"
        description="Default account to import transactions into."
        value={preferences.import_default_account_id || 0}
        options={accountOptions}
        onChange={(value) => onUpdate("import_default_account_id", value === 0 ? undefined : value)}
        saving={saving.import_default_account_id}
        isModified={isModified("import_default_account_id")}
        onReset={() => onReset("import_default_account_id")}
      />

      <SettingItem
        type="select"
        label="Duplicate Detection"
        description="How strictly to check for duplicate transactions."
        value={preferences.import_duplicate_strictness || "moderate"}
        options={duplicateStrictnessOptions}
        onChange={(value) => onUpdate("import_duplicate_strictness", value)}
        saving={saving.import_duplicate_strictness}
        isModified={isModified("import_duplicate_strictness")}
        onReset={() => onReset("import_duplicate_strictness")}
      />

      <SettingItem
        type="boolean"
        label="Auto-Apply Rules"
        description="Automatically apply matching rules during import."
        value={preferences.import_auto_apply_rules ?? true}
        onChange={(value) => onUpdate("import_auto_apply_rules", value)}
        saving={saving.import_auto_apply_rules}
        isModified={isModified("import_auto_apply_rules")}
        onReset={() => onReset("import_auto_apply_rules")}
      />

      <SettingItem
        type="boolean"
        label="Auto-Create Payees"
        description="Automatically create new payees during import."
        value={preferences.import_auto_create_payees ?? true}
        onChange={(value) => onUpdate("import_auto_create_payees", value)}
        saving={saving.import_auto_create_payees}
        isModified={isModified("import_auto_create_payees")}
        onReset={() => onReset("import_auto_create_payees")}
      />
    </div>
  );
}
