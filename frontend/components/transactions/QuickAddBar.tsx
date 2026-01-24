"use client";

import { useState, useEffect, useRef, KeyboardEvent } from "react";
import { transactionsAPI, accountsAPI, categoriesAPI } from "@/lib/api";
import { Account, Category, TransactionType, PayeeSuggestion } from "@/types";

interface QuickAddBarProps {
  onTransactionAdded: () => void;
}

export default function QuickAddBar({ onTransactionAdded }: QuickAddBarProps) {
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [payee, setPayee] = useState("");
  const [amount, setAmount] = useState("");
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [accountId, setAccountId] = useState<number | null>(null);
  const [transactionType, setTransactionType] = useState<TransactionType>(TransactionType.DEBIT);

  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [payeeSuggestions, setPayeeSuggestions] = useState<PayeeSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const payeeInputRef = useRef<HTMLInputElement>(null);
  const amountInputRef = useRef<HTMLInputElement>(null);

  // Load accounts and categories on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accountsData, categoriesData] = await Promise.all([
        accountsAPI.getAll(),
        categoriesAPI.getAll(),
      ]);
      setAccounts(accountsData);
      setCategories(categoriesData);

      // Set default account to first account
      if (accountsData.length > 0 && !accountId) {
        setAccountId(accountsData[0].id);
      }
    } catch (err) {
      console.error("Failed to load data:", err);
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
    if (!payee || !amount || !accountId) {
      setError("Please fill in payee, amount, and account");
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
        category_id: categoryId,
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

      // Focus payee input for next entry
      payeeInputRef.current?.focus();

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
      setPayee("");
      setAmount("");
      setCategoryId(null);
      setShowSuggestions(false);
      payeeInputRef.current?.focus();
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

  return (
    <div className="bg-white shadow rounded-lg p-4 mb-6">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Quick Add Transaction</h3>

      <div className="grid grid-cols-7 gap-3">
        {/* Date */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Date</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, () => payeeInputRef.current?.focus())}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Type Selector */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
          <select
            value={transactionType}
            onChange={(e) => {
              setTransactionType(e.target.value as TransactionType);
              // Clear category when switching types since different categories apply
              setCategoryId(null);
            }}
            onKeyDown={(e) => handleKeyDown(e, () => payeeInputRef.current?.focus())}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={TransactionType.DEBIT}>📤 Expense</option>
            <option value={TransactionType.CREDIT}>📥 Income</option>
            <option value={TransactionType.TRANSFER}>🔄 Transfer</option>
          </select>
        </div>

        {/* Payee with autocomplete */}
        <div className="relative">
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Payee <span className="text-red-500">*</span>
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
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
          {showSuggestions && payeeSuggestions.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
              {payeeSuggestions.map((suggestion) => (
                <div
                  key={suggestion.id}
                  onClick={() => handlePayeeSelect(suggestion)}
                  className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        {suggestion.canonical_name}
                      </div>
                      {suggestion.default_category_name && (
                        <div className="text-xs text-gray-500">
                          {suggestion.default_category_name}
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-gray-400 ml-2">
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
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Amount <span className="text-red-500">*</span>
          </label>
          <input
            ref={amountInputRef}
            type="text"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e)}
            placeholder="0.00"
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Category */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Category</label>
          <select
            value={categoryId || ""}
            onChange={(e) => setCategoryId(e.target.value ? parseInt(e.target.value) : null)}
            onKeyDown={(e) => handleKeyDown(e)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select...</option>
            {filteredCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>

        {/* Account */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Account <span className="text-red-500">*</span>
          </label>
          <select
            value={accountId || ""}
            onChange={(e) => setAccountId(e.target.value ? parseInt(e.target.value) : null)}
            onKeyDown={(e) => handleKeyDown(e)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select...</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </div>

        {/* Add Button */}
        <div className="flex items-end">
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !payee || !amount || !accountId}
            className={`w-full px-4 py-1.5 text-sm font-medium rounded-md ${
              success
                ? "bg-green-600 text-white"
                : "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            }`}
          >
            {success ? "✓ Added" : isSubmitting ? "Adding..." : "Add"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-2 text-xs text-red-600">{error}</div>
      )}

      <div className="mt-2 text-xs text-gray-500">
        Tip: Press <kbd className="px-1 py-0.5 bg-gray-100 border border-gray-300 rounded">Enter</kbd> to add, <kbd className="px-1 py-0.5 bg-gray-100 border border-gray-300 rounded">Esc</kbd> to clear
      </div>
    </div>
  );
}
