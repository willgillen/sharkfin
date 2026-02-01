"use client";

import { useState, useEffect, useRef, KeyboardEvent } from "react";
import { transactionsAPI, categoriesAPI } from "@/lib/api";
import { Category, TransactionType, PayeeSuggestion } from "@/types";

interface QuickAddBarProps {
  accountId: number;
  onTransactionAdded: () => void;
}

export default function QuickAddBar({ accountId, onTransactionAdded }: QuickAddBarProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [payee, setPayee] = useState("");
  const [amount, setAmount] = useState("");
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [transactionType, setTransactionType] = useState<TransactionType>(TransactionType.DEBIT);

  const [categories, setCategories] = useState<Category[]>([]);
  const [payeeSuggestions, setPayeeSuggestions] = useState<PayeeSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const payeeInputRef = useRef<HTMLInputElement>(null);
  const amountInputRef = useRef<HTMLInputElement>(null);

  // Load categories on mount
  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const categoriesData = await categoriesAPI.getAll();
      setCategories(categoriesData);
    } catch (err) {
      console.error("Failed to load categories:", err);
    }
  };

  // Fetch payee suggestions as user types
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (payee.length >= 2) {
        try {
          const suggestions = await transactionsAPI.getPayeeSuggestions(payee);
          setPayeeSuggestions(suggestions);
          setShowSuggestions(suggestions.length > 0);
        } catch (err) {
          console.error("Failed to fetch payee suggestions:", err);
        }
      } else {
        setPayeeSuggestions([]);
        setShowSuggestions(false);
      }
    };

    const debounce = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(debounce);
  }, [payee]);

  // Get category suggestion when payee is selected
  const handlePayeeSelect = (selectedPayee: PayeeSuggestion) => {
    setPayee(selectedPayee.canonical_name);
    setShowSuggestions(false);

    // Auto-fill category from payee's default category
    if (selectedPayee.default_category_id) {
      setCategoryId(selectedPayee.default_category_id);
    }

    // Focus amount input after selecting payee
    amountInputRef.current?.focus();
  };

  const handleSubmit = async () => {
    if (!payee || !amount) {
      setError("Please fill in payee and amount");
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      const parsedAmount = parseFloat(amount);
      if (isNaN(parsedAmount)) {
        throw new Error("Invalid amount");
      }

      await transactionsAPI.create({
        date,
        payee,
        amount: Math.abs(parsedAmount).toString(),
        account_id: accountId,
        category_id: categoryId ?? undefined,
        type: transactionType,
        description: "",
      });

      // Show success and reset form
      setSuccess(true);
      setTimeout(() => setSuccess(false), 1500);

      setPayee("");
      setAmount("");
      setCategoryId(null);
      setDate(new Date().toISOString().split("T")[0]);

      // Auto-collapse after successful add
      setTimeout(() => setIsExpanded(false), 1500);

      // Notify parent to refresh transaction list
      onTransactionAdded();
    } catch (err: any) {
      // Properly handle FastAPI validation errors
      let errorMessage = "Failed to add transaction";

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;

        // Check if it's a validation error array
        if (Array.isArray(detail)) {
          errorMessage = detail.map((e: any) => e.msg || JSON.stringify(e)).join(", ");
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (typeof detail === 'object') {
          errorMessage = JSON.stringify(detail);
        }
      }

      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent, nextField?: () => void) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (nextField) {
        nextField();
      } else {
        handleSubmit();
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      // ESC key to collapse
      setIsExpanded(false);
      setPayee("");
      setAmount("");
      setCategoryId(null);
      setShowSuggestions(false);
    }
  };

  // Filter categories based on transaction type
  const filteredCategories = categories.filter((c) => {
    if (transactionType === TransactionType.DEBIT) {
      return c.type === "expense";
    } else {
      return c.type === "income";
    }
  });

  // Auto-focus payee input when expanding
  useEffect(() => {
    if (isExpanded) {
      payeeInputRef.current?.focus();
    }
  }, [isExpanded]);

  return (
    <div className="bg-surface shadow rounded-lg mb-6 overflow-hidden transition-all duration-300">
      {!isExpanded ? (
        // Collapsed state: Single line button
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full px-4 py-3 text-left text-sm font-medium text-text-secondary hover:bg-surface-secondary transition-colors flex items-center gap-2"
        >
          <span className="text-primary-600 text-lg">+</span>
          Add Transaction
        </button>
      ) : (
        // Expanded state: Full form
        <div className="p-4 animate-slideDown">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-text-secondary">Quick Add Transaction</h3>
            <button
              onClick={() => setIsExpanded(false)}
              className="text-text-tertiary hover:text-text-secondary text-xl leading-none"
              title="Collapse (ESC)"
            >
              ×
            </button>
          </div>

          <div className="grid grid-cols-6 gap-3">
        {/* Date */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Date</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, () => payeeInputRef.current?.focus())}
            className="w-full px-2 py-1.5 text-sm text-text-primary border border-border rounded-md focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        {/* Type Selector */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Type</label>
          <select
            value={transactionType}
            onChange={(e) => {
              setTransactionType(e.target.value as TransactionType);
              // Clear category when switching types since different categories apply
              setCategoryId(null);
            }}
            onKeyDown={(e) => handleKeyDown(e, () => payeeInputRef.current?.focus())}
            className="w-full px-2 py-1.5 text-sm text-text-primary border border-border rounded-md focus:ring-primary-500 focus:border-primary-500"
          >
            <option value={TransactionType.DEBIT}>📤 Expense</option>
            <option value={TransactionType.CREDIT}>📥 Income</option>
            <option value={TransactionType.TRANSFER}>🔄 Transfer</option>
          </select>
        </div>

        {/* Payee with autocomplete */}
        <div className="relative">
          <label className="block text-xs font-medium text-text-secondary mb-1">
            Payee <span className="text-danger-500">*</span>
          </label>
          <input
            ref={payeeInputRef}
            type="text"
            value={payee}
            onChange={(e) => setPayee(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, () => amountInputRef.current?.focus())}
            onFocus={() => payee.length >= 2 && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder="e.g., Starbucks"
            className="w-full px-2 py-1.5 text-sm text-text-primary placeholder-text-disabled border border-border rounded-md focus:ring-primary-500 focus:border-primary-500"
          />
          {showSuggestions && payeeSuggestions.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-surface border border-border rounded-md shadow-lg max-h-60 overflow-y-auto">
              {payeeSuggestions.map((suggestion) => (
                <div
                  key={suggestion.id}
                  onClick={() => handlePayeeSelect(suggestion)}
                  className="px-3 py-2 hover:bg-surface-secondary cursor-pointer border-b border-border last:border-b-0"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-text-primary">
                        {suggestion.canonical_name}
                      </div>
                      {suggestion.default_category_name && (
                        <div className="text-xs text-text-tertiary">
                          {suggestion.default_category_name}
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-text-disabled ml-2">
                      {suggestion.transaction_count} txns
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Amount */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">
            Amount <span className="text-danger-500">*</span>
          </label>
          <input
            ref={amountInputRef}
            type="text"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e)}
            placeholder="0.00"
            className="w-full px-2 py-1.5 text-sm text-text-primary placeholder-text-disabled border border-border rounded-md focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        {/* Category */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Category</label>
          <select
            value={categoryId || ""}
            onChange={(e) => setCategoryId(e.target.value ? parseInt(e.target.value) : null)}
            onKeyDown={(e) => handleKeyDown(e)}
            className="w-full px-2 py-1.5 text-sm text-text-primary border border-border rounded-md focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">Select...</option>
            {filteredCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>

        {/* Add Button */}
        <div className="flex items-end">
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !payee || !amount}
            className={`w-full px-4 py-1.5 text-sm font-medium rounded-md ${
              success
                ? "bg-success-600 text-text-inverse"
                : "bg-primary-600 text-text-inverse hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            }`}
          >
            {success ? "✓ Added" : isSubmitting ? "Adding..." : "Add"}
          </button>
        </div>
      </div>

          {error && (
            <div className="mt-2 text-xs text-danger-600">{error}</div>
          )}

          <div className="mt-2 text-xs text-text-tertiary">
            Tip: Press <kbd className="px-1 py-0.5 bg-surface-secondary border border-border rounded">Enter</kbd> to add, <kbd className="px-1 py-0.5 bg-surface-secondary border border-border rounded">Esc</kbd> to collapse
          </div>
        </div>
      )}
    </div>
  );
}
