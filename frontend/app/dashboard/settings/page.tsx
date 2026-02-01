"use client";

import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/layout/DashboardLayout";
import IconProviderSettings from "@/components/settings/IconProviderSettings";
import ApiKeySettings from "@/components/settings/ApiKeySettings";
import { useAuth } from "@/lib/hooks/useAuth";
import { User } from "@/types";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [currentUser, setCurrentUser] = useState<User | null>(user);
  const [iconProviderKey, setIconProviderKey] = useState(0);

  useEffect(() => {
    setCurrentUser(user);
  }, [user]);

  const handleUserUpdate = (updatedUser: User) => {
    setCurrentUser(updatedUser);
    refreshUser();
  };

  // Refresh icon provider settings when API key changes
  const handleApiKeyUpdate = useCallback(() => {
    setIconProviderKey((k) => k + 1);
  }, []);

  if (!currentUser) {
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

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0">
        <h1 className="text-2xl font-semibold text-text-primary mb-8">Settings</h1>

        <div className="space-y-8">
          {/* API Key Settings */}
          <ApiKeySettings onUpdate={handleApiKeyUpdate} />

          {/* Icon Provider Settings */}
          <IconProviderSettings
            key={iconProviderKey}
            user={currentUser}
            onUpdate={handleUserUpdate}
          />
        </div>
      </div>
    </DashboardLayout>
  );
}
