"use client";

import { useState, useCallback } from "react";
import DashboardLayout from "@/components/layout/DashboardLayout";
import IconProviderSettings from "@/components/settings/IconProviderSettings";
import ApiKeySettings from "@/components/settings/ApiKeySettings";
import DisplayPreferences from "@/components/settings/DisplayPreferences";
import TransactionPreferences from "@/components/settings/TransactionPreferences";
import ImportPreferences from "@/components/settings/ImportPreferences";
import { useAuth } from "@/lib/hooks/useAuth";
import { usePreferences } from "@/lib/hooks/usePreferences";
import { User } from "@/types";

type SettingsCategory = "display" | "transactions" | "import" | "appearance" | "api-keys";

const CATEGORY_INFO: Record<SettingsCategory, { label: string; description: string }> = {
  display: {
    label: "Display",
    description: "Date, number, and currency formatting options.",
  },
  transactions: {
    label: "Transactions",
    description: "Transaction list and viewing preferences.",
  },
  import: {
    label: "Import",
    description: "Settings for importing transactions from files.",
  },
  appearance: {
    label: "Appearance",
    description: "Visual appearance and icon settings.",
  },
  "api-keys": {
    label: "API Keys",
    description: "Manage third-party service API keys.",
  },
};

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const {
    preferences,
    metadata,
    loading,
    error,
    saving,
    updatePreference,
    resetPreference,
    resetCategory,
    isModified,
  } = usePreferences();

  const [activeCategory, setActiveCategory] = useState<SettingsCategory>("display");
  const [currentUser, setCurrentUser] = useState<User | null>(user);
  const [iconProviderKey, setIconProviderKey] = useState(0);

  const handleUserUpdate = (updatedUser: User) => {
    setCurrentUser(updatedUser);
    refreshUser();
  };

  const handleApiKeyUpdate = useCallback(() => {
    setIconProviderKey((k) => k + 1);
  }, []);

  const categories: SettingsCategory[] = ["display", "transactions", "import", "appearance", "api-keys"];

  if (!user) {
    return (
      <DashboardLayout>
        <div className="px-4 sm:px-0">
          <div className="animate-pulse">
            <div className="h-8 bg-surface-secondary rounded w-1/4 mb-8"></div>
            <div className="h-64 bg-surface-secondary rounded"></div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const renderCategoryContent = () => {
    if (loading) {
      return (
        <div className="animate-pulse space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-surface-secondary rounded"></div>
          ))}
        </div>
      );
    }

    if (!preferences || !metadata) {
      return (
        <div className="text-center py-8 text-text-secondary">
          Failed to load preferences. Please try again.
        </div>
      );
    }

    switch (activeCategory) {
      case "display":
        return (
          <DisplayPreferences
            preferences={preferences}
            metadata={metadata}
            saving={saving}
            onUpdate={updatePreference}
            onReset={resetPreference}
            isModified={isModified}
          />
        );

      case "transactions":
        return (
          <TransactionPreferences
            preferences={preferences}
            metadata={metadata}
            saving={saving}
            onUpdate={updatePreference}
            onReset={resetPreference}
            isModified={isModified}
          />
        );

      case "import":
        return (
          <ImportPreferences
            preferences={preferences}
            metadata={metadata}
            saving={saving}
            onUpdate={updatePreference}
            onReset={resetPreference}
            isModified={isModified}
          />
        );

      case "appearance":
        return (
          <IconProviderSettings
            key={iconProviderKey}
            user={currentUser || user}
            onUpdate={handleUserUpdate}
          />
        );

      case "api-keys":
        return <ApiKeySettings onUpdate={handleApiKeyUpdate} />;

      default:
        return null;
    }
  };

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0">
        <h1 className="text-2xl font-semibold text-text-primary mb-8">Settings</h1>

        {error && (
          <div className="mb-6 p-4 bg-danger-50 border border-danger-200 rounded-md text-sm text-danger-600">
            {error}
          </div>
        )}

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar navigation */}
          <nav className="lg:w-48 flex-shrink-0">
            <ul className="space-y-1">
              {categories.map((category) => (
                <li key={category}>
                  <button
                    onClick={() => setActiveCategory(category)}
                    className={`w-full text-left px-4 py-2 rounded-md text-sm font-medium transition-colors
                      ${
                        activeCategory === category
                          ? "bg-primary-50 text-primary-700 border-l-2 border-primary-600"
                          : "text-text-secondary hover:bg-surface-secondary hover:text-text-primary"
                      }`}
                  >
                    {CATEGORY_INFO[category].label}
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          {/* Main content area */}
          <div className="flex-1 min-w-0">
            <div className="bg-surface rounded-lg shadow-sm border border-border">
              {/* Category header */}
              <div className="px-6 py-4 border-b border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-medium text-text-primary">
                      {CATEGORY_INFO[activeCategory].label}
                    </h2>
                    <p className="mt-1 text-sm text-text-secondary">
                      {CATEGORY_INFO[activeCategory].description}
                    </p>
                  </div>
                  {activeCategory !== "api-keys" && activeCategory !== "appearance" && (
                    <button
                      onClick={() => resetCategory(activeCategory)}
                      disabled={saving[`category_${activeCategory}`]}
                      className="text-sm text-text-tertiary hover:text-text-secondary disabled:opacity-50"
                    >
                      {saving[`category_${activeCategory}`] ? "Resetting..." : "Reset to defaults"}
                    </button>
                  )}
                </div>
              </div>

              {/* Category content */}
              <div className="px-6 py-2">{renderCategoryContent()}</div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
