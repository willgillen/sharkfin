"use client";

import { useState, useEffect } from "react";
import { payeesAPI } from "@/lib/api/payees";
import { IconSuggestion } from "@/types";
import { PayeeIcon, PayeeIconLarge } from "./PayeeIcon";

interface IconPickerProps {
  /** Current logo_url value */
  value: string | null;
  /** Payee name for suggestions */
  payeeName: string;
  /** Callback when icon is selected */
  onChange: (logoUrl: string | null) => void;
  /** Whether the picker is disabled */
  disabled?: boolean;
}

// Common emoji options for quick selection
const COMMON_EMOJIS = [
  { emoji: "🏪", label: "Store" },
  { emoji: "🍽️", label: "Restaurant" },
  { emoji: "☕", label: "Coffee" },
  { emoji: "🛒", label: "Grocery" },
  { emoji: "⛽", label: "Gas" },
  { emoji: "🏥", label: "Medical" },
  { emoji: "🏦", label: "Bank" },
  { emoji: "🏠", label: "Home" },
  { emoji: "💼", label: "Business" },
  { emoji: "🎬", label: "Entertainment" },
  { emoji: "✈️", label: "Travel" },
  { emoji: "💪", label: "Fitness" },
  { emoji: "📱", label: "Tech" },
  { emoji: "🛍️", label: "Shopping" },
  { emoji: "🔧", label: "Services" },
  { emoji: "📚", label: "Education" },
];

/**
 * IconPicker component - allows selecting or suggesting icons for payees.
 *
 * Features:
 * - Auto-suggests brand logo or emoji based on payee name
 * - Quick emoji picker for common categories
 * - Custom URL input for other images
 * - Preview of current selection
 */
export function IconPicker({ value, payeeName, onChange, disabled = false }: IconPickerProps) {
  const [suggestion, setSuggestion] = useState<IconSuggestion | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customUrl, setCustomUrl] = useState("");
  const [activeTab, setActiveTab] = useState<"suggested" | "emoji" | "custom">("suggested");

  // Fetch icon suggestion when payee name changes
  useEffect(() => {
    if (!payeeName || payeeName.length < 2) {
      setSuggestion(null);
      return;
    }

    const fetchSuggestion = async () => {
      setLoading(true);
      try {
        const result = await payeesAPI.suggestIcon(payeeName);
        setSuggestion(result);
      } catch (error) {
        console.error("Failed to fetch icon suggestion:", error);
        setSuggestion(null);
      } finally {
        setLoading(false);
      }
    };

    // Debounce the API call
    const timeout = setTimeout(fetchSuggestion, 300);
    return () => clearTimeout(timeout);
  }, [payeeName]);

  const handleUseSuggestion = () => {
    if (suggestion) {
      onChange(suggestion.icon_value);
    }
  };

  const handleSelectEmoji = (emoji: string) => {
    onChange(`emoji:${emoji}`);
  };

  const handleCustomUrl = () => {
    if (customUrl.trim()) {
      onChange(customUrl.trim());
      setCustomUrl("");
      setShowCustomInput(false);
    }
  };

  const handleClear = () => {
    onChange(null);
  };

  return (
    <div className="space-y-4">
      {/* Current Icon Preview */}
      <div className="flex items-center gap-4">
        <PayeeIconLarge logoUrl={value} name={payeeName || "Payee"} />
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-700">Current Icon</p>
          <p className="text-xs text-gray-500">
            {value ? (
              value.startsWith("emoji:") ? `Emoji: ${value.slice(6)}` : "Custom image"
            ) : (
              "No icon set (using default)"
            )}
          </p>
        </div>
        {value && !disabled && (
          <button
            type="button"
            onClick={handleClear}
            className="text-sm text-red-600 hover:text-red-700"
          >
            Clear
          </button>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px space-x-8">
          <button
            type="button"
            onClick={() => setActiveTab("suggested")}
            className={`py-2 px-1 text-sm font-medium border-b-2 ${
              activeTab === "suggested"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
            disabled={disabled}
          >
            Suggested
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("emoji")}
            className={`py-2 px-1 text-sm font-medium border-b-2 ${
              activeTab === "emoji"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
            disabled={disabled}
          >
            Emoji
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("custom")}
            className={`py-2 px-1 text-sm font-medium border-b-2 ${
              activeTab === "custom"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
            disabled={disabled}
          >
            Custom URL
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[120px]">
        {/* Suggested Tab */}
        {activeTab === "suggested" && (
          <div className="space-y-3">
            {loading ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-sm text-gray-500">Finding icon...</span>
              </div>
            ) : suggestion ? (
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-4">
                  <PayeeIcon logoUrl={suggestion.icon_value} name={payeeName} size={48} />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {suggestion.icon_type === "brand" ? "Brand Logo" : "Emoji Suggestion"}
                    </p>
                    <p className="text-xs text-gray-500">
                      {suggestion.matched_term
                        ? `Matched: "${suggestion.matched_term}"`
                        : "Best match for this payee"}
                    </p>
                    <p className="text-xs text-gray-400">
                      Confidence: {Math.round(suggestion.confidence * 100)}%
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleUseSuggestion}
                    disabled={disabled}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Use This
                  </button>
                </div>
                {suggestion.icon_type === "brand" && suggestion.brand_color && (
                  <div className="mt-2 flex items-center gap-2">
                    <span
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: suggestion.brand_color }}
                    />
                    <span className="text-xs text-gray-500">
                      Brand color: {suggestion.brand_color}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <p className="text-sm">Enter a payee name to get icon suggestions</p>
              </div>
            )}
          </div>
        )}

        {/* Emoji Tab */}
        {activeTab === "emoji" && (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">Select a category emoji:</p>
            <div className="grid grid-cols-8 gap-2">
              {COMMON_EMOJIS.map(({ emoji, label }) => (
                <button
                  key={emoji}
                  type="button"
                  onClick={() => handleSelectEmoji(emoji)}
                  disabled={disabled}
                  className={`p-2 text-2xl rounded-lg hover:bg-gray-100 transition-colors ${
                    value === `emoji:${emoji}` ? "bg-blue-100 ring-2 ring-blue-500" : "bg-gray-50"
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                  title={label}
                >
                  {emoji}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Tip: The system will also suggest emojis automatically based on the payee name.
            </p>
          </div>
        )}

        {/* Custom URL Tab */}
        {activeTab === "custom" && (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">Enter a custom image URL:</p>
            <div className="flex gap-2">
              <input
                type="url"
                value={customUrl}
                onChange={(e) => setCustomUrl(e.target.value)}
                placeholder="https://example.com/logo.png"
                disabled={disabled}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
              <button
                type="button"
                onClick={handleCustomUrl}
                disabled={disabled || !customUrl.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Use
              </button>
            </div>
            <p className="text-xs text-gray-400">
              Supported formats: PNG, JPG, GIF, SVG, WebP
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
