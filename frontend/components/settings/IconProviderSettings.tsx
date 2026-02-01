"use client";

import { useState, useEffect } from "react";
import { usersAPI } from "@/lib/api/users";
import { settingsAPI } from "@/lib/api/settings";
import { IconProviderStatus, IconProvider, User } from "@/types";

interface IconProviderSettingsProps {
  user: User;
  onUpdate?: (user: User) => void;
}

export default function IconProviderSettings({ user, onUpdate }: IconProviderSettingsProps) {
  const [providerStatus, setProviderStatus] = useState<IconProviderStatus | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<IconProvider>(
    user.ui_preferences?.icon_provider || "simple_icons"
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadProviderStatus();
  }, []);

  const loadProviderStatus = async () => {
    try {
      const status = await settingsAPI.getIconProviders();
      setProviderStatus(status);
    } catch (err) {
      console.error("Failed to load icon provider status:", err);
    }
  };

  const handleProviderChange = async (provider: IconProvider) => {
    setSelectedProvider(provider);
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const updatedUser = await usersAPI.updatePreferences({
        icon_provider: provider,
      });
      setSuccess(true);
      onUpdate?.(updatedUser);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError("Failed to save preference. Please try again.");
      setSelectedProvider(user.ui_preferences?.icon_provider || "simple_icons");
    } finally {
      setSaving(false);
    }
  };

  if (!providerStatus) {
    return (
      <div className="bg-surface rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-surface-secondary rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-surface-secondary rounded w-2/3 mb-6"></div>
          <div className="space-y-4">
            <div className="h-20 bg-surface-secondary rounded"></div>
            <div className="h-20 bg-surface-secondary rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const logoDevAvailable = providerStatus.providers.logo_dev.available;

  return (
    <div className="bg-surface rounded-lg p-6">
      <h3 className="text-lg font-medium text-text-primary mb-2">Icon Provider</h3>
      <p className="text-sm text-text-secondary mb-6">
        Choose how merchant and payee logos are displayed in the application.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-danger-50 border border-danger-200 rounded-md text-sm text-danger-600">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-success-50 border border-success-200 rounded-md text-sm text-success-600">
          Preference saved successfully!
        </div>
      )}

      <div className="space-y-4">
        {/* Simple Icons Option */}
        <label
          className={`flex items-start p-4 border rounded-lg cursor-pointer transition-colors ${
            selectedProvider === "simple_icons"
              ? "border-primary-500 bg-primary-50"
              : "border-border hover:border-primary-300"
          }`}
        >
          <input
            type="radio"
            name="icon_provider"
            value="simple_icons"
            checked={selectedProvider === "simple_icons"}
            onChange={() => handleProviderChange("simple_icons")}
            disabled={saving}
            className="mt-1 h-4 w-4 text-primary-600 border-border focus:ring-primary-500"
          />
          <div className="ml-3 flex-1">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-text-primary">Simple Icons</span>
              <span className="text-xs px-2 py-1 bg-success-100 text-success-700 rounded-full">
                Default
              </span>
            </div>
            <p className="mt-1 text-sm text-text-secondary">
              {providerStatus.providers.simple_icons.description}
            </p>
            <div className="mt-2 flex items-center gap-4 text-xs text-text-tertiary">
              <span>No API key required</span>
              <span>No attribution required</span>
            </div>
          </div>
        </label>

        {/* Logo.dev Option */}
        <label
          className={`flex items-start p-4 border rounded-lg transition-colors ${
            logoDevAvailable
              ? selectedProvider === "logo_dev"
                ? "border-primary-500 bg-primary-50 cursor-pointer"
                : "border-border hover:border-primary-300 cursor-pointer"
              : "border-border bg-surface-secondary cursor-not-allowed opacity-60"
          }`}
        >
          <input
            type="radio"
            name="icon_provider"
            value="logo_dev"
            checked={selectedProvider === "logo_dev"}
            onChange={() => handleProviderChange("logo_dev")}
            disabled={!logoDevAvailable || saving}
            className="mt-1 h-4 w-4 text-primary-600 border-border focus:ring-primary-500"
          />
          <div className="ml-3 flex-1">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-text-primary">Logo.dev</span>
              {!logoDevAvailable && (
                <span className="text-xs px-2 py-1 bg-warning-100 text-warning-700 rounded-full">
                  Not Configured
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-text-secondary">
              {providerStatus.providers.logo_dev.description}
            </p>
            {logoDevAvailable ? (
              <div className="mt-2 flex items-center gap-4 text-xs text-text-tertiary">
                <span>API key configured</span>
                {providerStatus.providers.logo_dev.requires_attribution && (
                  <span className="text-warning-600">Attribution required</span>
                )}
              </div>
            ) : (
              <p className="mt-2 text-xs text-text-tertiary">
                To enable Logo.dev, set the LOGO_DEV_API_KEY environment variable on the server.
                Get an API key at{" "}
                <a
                  href="https://logo.dev"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  logo.dev
                </a>
              </p>
            )}
          </div>
        </label>
      </div>

      {selectedProvider === "logo_dev" && providerStatus.providers.logo_dev.requires_attribution && (
        <div className="mt-4 p-3 bg-warning-50 border border-warning-200 rounded-md">
          <p className="text-sm text-warning-700">
            <strong>Attribution Required:</strong> When using Logo.dev on the free tier, logos
            will include a small attribution link as per their terms of service.
          </p>
        </div>
      )}

      {saving && (
        <div className="mt-4 flex items-center text-sm text-text-secondary">
          <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Saving...
        </div>
      )}
    </div>
  );
}
