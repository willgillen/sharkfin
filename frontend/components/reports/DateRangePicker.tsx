"use client";

import { useState, useRef, useEffect } from "react";

export type DateRangePreset =
  | "mtd"      // Month to date
  | "last_month"
  | "qtd"      // Quarter to date
  | "ytd"      // Year to date
  | "last_30"
  | "last_90"
  | "last_12_months"
  | "all_time"
  | "custom";

export interface DateRange {
  startDate: string;
  endDate: string;
  preset: DateRangePreset;
}

interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
}

const PRESETS: { value: DateRangePreset; label: string }[] = [
  { value: "mtd", label: "Month to Date" },
  { value: "last_month", label: "Last Month" },
  { value: "qtd", label: "Quarter to Date" },
  { value: "ytd", label: "Year to Date" },
  { value: "last_30", label: "Last 30 Days" },
  { value: "last_90", label: "Last 90 Days" },
  { value: "last_12_months", label: "Last 12 Months" },
  { value: "all_time", label: "All Time" },
  { value: "custom", label: "Custom Range" },
];

function getPresetDates(preset: DateRangePreset): { startDate: string; endDate: string } {
  const today = new Date();
  const endDate = today.toISOString().split("T")[0];

  switch (preset) {
    case "mtd": {
      const startDate = new Date(today.getFullYear(), today.getMonth(), 1);
      return { startDate: startDate.toISOString().split("T")[0], endDate };
    }
    case "last_month": {
      const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      const lastDayOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
      return {
        startDate: lastMonth.toISOString().split("T")[0],
        endDate: lastDayOfLastMonth.toISOString().split("T")[0],
      };
    }
    case "qtd": {
      const quarter = Math.floor(today.getMonth() / 3);
      const startDate = new Date(today.getFullYear(), quarter * 3, 1);
      return { startDate: startDate.toISOString().split("T")[0], endDate };
    }
    case "ytd": {
      const startDate = new Date(today.getFullYear(), 0, 1);
      return { startDate: startDate.toISOString().split("T")[0], endDate };
    }
    case "last_30": {
      const startDate = new Date(today);
      startDate.setDate(startDate.getDate() - 30);
      return { startDate: startDate.toISOString().split("T")[0], endDate };
    }
    case "last_90": {
      const startDate = new Date(today);
      startDate.setDate(startDate.getDate() - 90);
      return { startDate: startDate.toISOString().split("T")[0], endDate };
    }
    case "last_12_months": {
      const startDate = new Date(today);
      startDate.setFullYear(startDate.getFullYear() - 1);
      return { startDate: startDate.toISOString().split("T")[0], endDate };
    }
    case "all_time": {
      // Return a very old date for "all time"
      return { startDate: "2000-01-01", endDate };
    }
    case "custom":
    default:
      return { startDate: "", endDate };
  }
}

export function getDefaultDateRange(): DateRange {
  const dates = getPresetDates("ytd");
  return {
    ...dates,
    preset: "ytd",
  };
}

export default function DateRangePicker({ value, onChange }: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showCustomInputs, setShowCustomInputs] = useState(value.preset === "custom");
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  const handlePresetChange = (preset: DateRangePreset) => {
    if (preset === "custom") {
      setShowCustomInputs(true);
      onChange({ ...value, preset: "custom" });
    } else {
      setShowCustomInputs(false);
      const dates = getPresetDates(preset);
      onChange({ ...dates, preset });
      setIsOpen(false);
    }
  };

  const handleCustomDateChange = (field: "startDate" | "endDate", dateValue: string) => {
    onChange({
      ...value,
      [field]: dateValue,
      preset: "custom",
    });
  };

  const formatDisplayDate = (dateStr: string) => {
    if (!dateStr) return "";
    const date = new Date(dateStr + "T00:00:00");
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  const getDisplayText = () => {
    if (value.preset === "all_time") {
      return "All Time";
    }
    if (value.preset !== "custom") {
      const preset = PRESETS.find((p) => p.value === value.preset);
      return preset?.label || "";
    }
    if (value.startDate && value.endDate) {
      return `${formatDisplayDate(value.startDate)} - ${formatDisplayDate(value.endDate)}`;
    }
    return "Select dates";
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-4 py-2 border border-border rounded-lg bg-surface text-text-primary hover:bg-surface-secondary transition-colors"
      >
        <svg className="w-5 h-5 text-text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <span className="font-medium">{getDisplayText()}</span>
        <svg
          className={`w-4 h-4 text-text-tertiary transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full mt-2 w-72 bg-surface border border-border rounded-lg shadow-lg z-50">
          <div className="p-2">
            <div className="text-xs font-semibold text-text-tertiary uppercase tracking-wider px-2 py-1">
              Quick Select
            </div>
            <div className="grid grid-cols-2 gap-1">
              {PRESETS.filter((p) => p.value !== "custom").map((preset) => (
                <button
                  key={preset.value}
                  onClick={() => handlePresetChange(preset.value)}
                  className={`px-3 py-2 text-sm rounded-md text-left transition-colors ${
                    value.preset === preset.value
                      ? "bg-primary-100 text-primary-700 font-medium"
                      : "text-text-primary hover:bg-surface-secondary"
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          <div className="border-t border-border p-2">
            <button
              onClick={() => handlePresetChange("custom")}
              className={`w-full px-3 py-2 text-sm rounded-md text-left transition-colors ${
                value.preset === "custom"
                  ? "bg-primary-100 text-primary-700 font-medium"
                  : "text-text-primary hover:bg-surface-secondary"
              }`}
            >
              Custom Range
            </button>

            {showCustomInputs && (
              <div className="mt-2 space-y-2 px-1">
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={value.startDate}
                    onChange={(e) => handleCustomDateChange("startDate", e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-border rounded-md bg-surface text-text-primary focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={value.endDate}
                    onChange={(e) => handleCustomDateChange("endDate", e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-border rounded-md bg-surface text-text-primary focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  disabled={!value.startDate || !value.endDate}
                  className="w-full mt-2 px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Apply
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
