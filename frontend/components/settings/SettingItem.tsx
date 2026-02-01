"use client";

import { useState } from "react";

interface SelectOption {
  value: string | number | boolean;
  label: string;
}

interface BaseSettingItemProps {
  label: string;
  description?: string;
  disabled?: boolean;
  saving?: boolean;
  onReset?: () => void;
  isModified?: boolean;
}

interface SelectSettingProps extends BaseSettingItemProps {
  type: "select";
  value: string | number;
  options: SelectOption[];
  onChange: (value: string | number) => void;
}

interface BooleanSettingProps extends BaseSettingItemProps {
  type: "boolean";
  value: boolean;
  onChange: (value: boolean) => void;
}

interface NumberSettingProps extends BaseSettingItemProps {
  type: "number";
  value: number;
  min?: number;
  max?: number;
  onChange: (value: number) => void;
}

interface StringSettingProps extends BaseSettingItemProps {
  type: "string";
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
}

type SettingItemProps =
  | SelectSettingProps
  | BooleanSettingProps
  | NumberSettingProps
  | StringSettingProps;

export default function SettingItem(props: SettingItemProps) {
  const { label, description, disabled, saving, onReset, isModified } = props;

  const renderInput = () => {
    switch (props.type) {
      case "select":
        return (
          <select
            value={String(props.value)}
            onChange={(e) => {
              const option = props.options.find((o) => String(o.value) === e.target.value);
              if (option) {
                props.onChange(option.value as string | number);
              }
            }}
            disabled={disabled || saving}
            className="w-full sm:w-auto px-3 py-2 border border-border rounded-md text-sm
                     bg-surface text-text-primary
                     focus:ring-primary-500 focus:border-primary-500
                     disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {props.options.map((option) => (
              <option key={String(option.value)} value={String(option.value)}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case "boolean":
        return (
          <button
            type="button"
            role="switch"
            aria-checked={props.value}
            onClick={() => props.onChange(!props.value)}
            disabled={disabled || saving}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent
                      transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                      disabled:opacity-50 disabled:cursor-not-allowed
                      ${props.value ? "bg-primary-600" : "bg-gray-300"}`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0
                        transition duration-200 ease-in-out
                        ${props.value ? "translate-x-5" : "translate-x-0"}`}
            />
          </button>
        );

      case "number":
        return (
          <input
            type="number"
            value={props.value}
            min={props.min}
            max={props.max}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              if (!isNaN(val)) {
                props.onChange(val);
              }
            }}
            disabled={disabled || saving}
            className="w-24 px-3 py-2 border border-border rounded-md text-sm
                     bg-surface text-text-primary
                     focus:ring-primary-500 focus:border-primary-500
                     disabled:opacity-50 disabled:cursor-not-allowed"
          />
        );

      case "string":
        return (
          <input
            type="text"
            value={props.value}
            placeholder={props.placeholder}
            onChange={(e) => props.onChange(e.target.value)}
            disabled={disabled || saving}
            className="w-full sm:w-64 px-3 py-2 border border-border rounded-md text-sm
                     bg-surface text-text-primary
                     focus:ring-primary-500 focus:border-primary-500
                     disabled:opacity-50 disabled:cursor-not-allowed"
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between py-4 gap-3 sm:gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-text-primary">{label}</label>
          {isModified && (
            <span className="text-xs px-1.5 py-0.5 bg-primary-100 text-primary-700 rounded">
              Modified
            </span>
          )}
          {saving && (
            <svg
              className="animate-spin h-4 w-4 text-primary-600"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          )}
        </div>
        {description && (
          <p className="mt-1 text-sm text-text-secondary">{description}</p>
        )}
      </div>
      <div className="flex items-center gap-2">
        {renderInput()}
        {onReset && isModified && (
          <button
            type="button"
            onClick={onReset}
            disabled={disabled || saving}
            className="text-xs text-text-tertiary hover:text-text-secondary disabled:opacity-50"
            title="Reset to default"
          >
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
