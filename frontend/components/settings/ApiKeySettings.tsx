"use client";

import { useState, useEffect } from "react";
import { settingsAPI } from "@/lib/api/settings";
import { LogoDevSettings } from "@/types";

interface ApiKeySettingsProps {
  onUpdate?: () => void;
}

export default function ApiKeySettings({ onUpdate }: ApiKeySettingsProps) {
  const [logoDevSettings, setLogoDevSettings] = useState<LogoDevSettings | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const settings = await settingsAPI.getLogoDevSettings();
      setLogoDevSettings(settings);
    } catch (err) {
      console.error("Failed to load Logo.dev settings:", err);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const updatedSettings = await settingsAPI.updateLogoDevSettings({
        api_key: apiKey || null,
      });
      setLogoDevSettings(updatedSettings);
      setSuccess(true);
      setIsEditing(false);
      setApiKey("");
      onUpdate?.();
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError("Failed to save API key. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleClear = async () => {
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const updatedSettings = await settingsAPI.updateLogoDevSettings({
        api_key: "",
      });
      setLogoDevSettings(updatedSettings);
      setSuccess(true);
      setIsEditing(false);
      setApiKey("");
      onUpdate?.();
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError("Failed to clear API key. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  if (!logoDevSettings) {
    return (
      <div className="bg-surface rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-surface-secondary rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-surface-secondary rounded w-2/3 mb-6"></div>
          <div className="h-10 bg-surface-secondary rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface rounded-lg p-6">
      <h3 className="text-lg font-medium text-text-primary mb-2">API Keys</h3>
      <p className="text-sm text-text-secondary mb-6">
        Configure API keys for third-party services.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-danger-50 border border-danger-200 rounded-md text-sm text-danger-600">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-success-50 border border-success-200 rounded-md text-sm text-success-600">
          Settings saved successfully!
        </div>
      )}

      {/* Logo.dev API Key */}
      <div className="border border-border rounded-lg p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h4 className="text-sm font-medium text-text-primary">Logo.dev API Key</h4>
            <p className="text-xs text-text-secondary mt-1">
              {logoDevSettings.description}
            </p>
          </div>
          {logoDevSettings.api_key_configured && (
            <span className="text-xs px-2 py-1 bg-success-100 text-success-700 rounded-full">
              Configured
            </span>
          )}
        </div>

        {isEditing ? (
          <div className="space-y-3">
            <div className="relative">
              <input
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your Logo.dev API key"
                className="w-full px-3 py-2 pr-10 border border-border rounded-md text-sm focus:ring-primary-500 focus:border-primary-500"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary"
              >
                {showApiKey ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving || !apiKey.trim()}
                className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? "Saving..." : "Save"}
              </button>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setApiKey("");
                }}
                disabled={saving}
                className="px-4 py-2 border border-border text-text-primary text-sm font-medium rounded-md hover:bg-surface-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-md hover:bg-primary-700"
            >
              {logoDevSettings.api_key_configured ? "Update API Key" : "Add API Key"}
            </button>
            {logoDevSettings.api_key_configured && (
              <button
                onClick={handleClear}
                disabled={saving}
                className="px-4 py-2 border border-danger-300 text-danger-600 text-sm font-medium rounded-md hover:bg-danger-50"
              >
                {saving ? "Clearing..." : "Clear"}
              </button>
            )}
          </div>
        )}

        <p className="mt-3 text-xs text-text-tertiary">
          Get your API key from{" "}
          <a
            href="https://logo.dev"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:underline"
          >
            logo.dev
          </a>
          . Free tier includes 500K requests/month.
        </p>
      </div>
    </div>
  );
}
