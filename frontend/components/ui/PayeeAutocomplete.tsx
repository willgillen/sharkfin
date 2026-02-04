"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { PayeeWithCategory, PayeeCreate } from "@/types";
import { payeesAPI } from "@/lib/api";

export interface PayeeAutocompleteProps {
  label?: string;
  value?: PayeeWithCategory | null;
  inputValue?: string;
  onSelect: (payee: PayeeWithCategory | null) => void;
  onInputChange?: (value: string) => void;
  onCreateNew?: (name: string) => void;
  error?: string;
  helperText?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
}

export default function PayeeAutocomplete({
  label,
  value,
  inputValue: externalInputValue,
  onSelect,
  onInputChange,
  onCreateNew,
  error,
  helperText,
  placeholder = "Search or create payee...",
  required,
  disabled,
}: PayeeAutocompleteProps) {
  const [inputValue, setInputValue] = useState(externalInputValue || value?.canonical_name || "");
  const [suggestions, setSuggestions] = useState<PayeeWithCategory[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [creating, setCreating] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout>();

  // Sync external inputValue if provided
  useEffect(() => {
    if (externalInputValue !== undefined) {
      setInputValue(externalInputValue);
    }
  }, [externalInputValue]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const searchPayees = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      const results = await payeesAPI.autocomplete(query, 8);
      setSuggestions(results);
    } catch (err) {
      console.error("Failed to search payees:", err);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setIsOpen(true);
    setHighlightedIndex(-1);
    onInputChange?.(newValue);

    // Clear existing debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Debounce search
    debounceRef.current = setTimeout(() => {
      searchPayees(newValue);
    }, 200);
  };

  const handleSelect = (payee: PayeeWithCategory) => {
    setInputValue(payee.canonical_name);
    onSelect(payee);
    setIsOpen(false);
    setSuggestions([]);
  };

  const handleCreateNew = async () => {
    if (!inputValue.trim() || creating) return;

    setCreating(true);
    try {
      const newPayee = await payeesAPI.create({
        canonical_name: inputValue.trim(),
      });
      // Fetch the full payee with category info
      const fullPayee: PayeeWithCategory = {
        ...newPayee,
        default_category_name: null,
      };
      setInputValue(fullPayee.canonical_name);
      onSelect(fullPayee);
      onCreateNew?.(fullPayee.canonical_name);
      setIsOpen(false);
      setSuggestions([]);
    } catch (err) {
      console.error("Failed to create payee:", err);
    } finally {
      setCreating(false);
    }
  };

  const handleClear = () => {
    setInputValue("");
    onSelect(null);
    onInputChange?.("");
    setSuggestions([]);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === "ArrowDown" || e.key === "Enter") {
        setIsOpen(true);
        searchPayees(inputValue);
      }
      return;
    }

    const totalItems = suggestions.length + (inputValue.trim() ? 1 : 0); // +1 for "Create new"

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setHighlightedIndex((prev) => (prev < totalItems - 1 ? prev + 1 : prev));
        break;
      case "ArrowUp":
        e.preventDefault();
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case "Enter":
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
          handleSelect(suggestions[highlightedIndex]);
        } else if (highlightedIndex === suggestions.length && inputValue.trim()) {
          handleCreateNew();
        }
        break;
      case "Escape":
        setIsOpen(false);
        break;
    }
  };

  const showCreateOption = inputValue.trim() &&
    !suggestions.some(s => s.canonical_name.toLowerCase() === inputValue.trim().toLowerCase());

  return (
    <div className="w-full relative">
      {label && (
        <label className="block text-sm font-medium text-text-secondary mb-1">
          {label}
          {required && <span className="text-danger-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => {
            setIsOpen(true);
            if (inputValue) searchPayees(inputValue);
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={`
            block w-full px-3 py-2 pr-20
            text-text-primary
            placeholder-text-disabled
            bg-surface
            border border-border rounded-md shadow-sm
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
            disabled:bg-surface-secondary disabled:text-text-disabled disabled:cursor-not-allowed
            ${error ? "border-danger-300 focus:ring-danger-500 focus:border-danger-500" : ""}
          `}
        />
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 gap-1">
          {loading && (
            <svg className="animate-spin h-4 w-4 text-text-tertiary" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          )}
          {inputValue && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 text-text-tertiary hover:text-text-secondary rounded"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              setIsOpen(!isOpen);
              if (!isOpen) searchPayees(inputValue);
            }}
            disabled={disabled}
            className="p-1 text-text-tertiary hover:text-text-secondary rounded disabled:opacity-50"
          >
            <svg className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && (suggestions.length > 0 || showCreateOption) && (
        <div
          ref={dropdownRef}
          className="absolute z-50 mt-1 w-full bg-surface border border-border rounded-md shadow-lg max-h-60 overflow-auto"
        >
          {suggestions.map((payee, index) => (
            <button
              key={payee.id}
              type="button"
              onClick={() => handleSelect(payee)}
              className={`
                w-full px-3 py-2 text-left flex items-center justify-between gap-2
                ${highlightedIndex === index ? "bg-primary-50 text-primary-700" : "hover:bg-surface-secondary"}
              `}
            >
              <div className="flex-1 min-w-0">
                <div className="font-medium text-text-primary truncate">
                  {payee.canonical_name}
                </div>
                {payee.default_category_name && (
                  <div className="text-xs text-text-tertiary truncate">
                    {payee.default_category_name}
                  </div>
                )}
              </div>
            </button>
          ))}

          {showCreateOption && (
            <button
              type="button"
              onClick={handleCreateNew}
              disabled={creating}
              className={`
                w-full px-3 py-2 text-left flex items-center gap-2 border-t border-border
                ${highlightedIndex === suggestions.length ? "bg-primary-50 text-primary-700" : "hover:bg-surface-secondary"}
                ${creating ? "opacity-50 cursor-not-allowed" : ""}
              `}
            >
              <svg className="h-4 w-4 text-primary-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span className="truncate">
                {creating ? "Creating..." : `Create "${inputValue.trim()}"`}
              </span>
            </button>
          )}
        </div>
      )}

      {error && (
        <p className="mt-1 text-sm text-danger-600">{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-1 text-sm text-text-tertiary">{helperText}</p>
      )}
    </div>
  );
}
