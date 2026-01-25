"use client";

import { useState } from "react";
import { Account, AccountCreate, AccountUpdate, AccountType } from "@/types";
import { Input, Select, Textarea } from "@/components/ui";

interface AccountFormProps {
  account?: Account;
  onSubmit: (data: AccountCreate | AccountUpdate) => Promise<void>;
  onCancel: () => void;
}

export default function AccountForm({ account, onSubmit, onCancel }: AccountFormProps) {
  const [formData, setFormData] = useState({
    name: account?.name || "",
    type: account?.type || AccountType.CHECKING,
    institution: account?.institution || "",
    account_number: account?.account_number || "",
    opening_balance: account?.opening_balance || "0.00",
    opening_balance_date: account?.opening_balance_date || "",
    currency: account?.currency || "USD",
    is_active: account?.is_active !== undefined ? account.is_active : true,
    notes: account?.notes || "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await onSubmit(formData);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save account");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Input
            label="Account Name"
            id="name"
            name="name"
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Main Checking, Emergency Savings"
          />
        </div>

        <div>
          <Select
            label="Account Type"
            id="type"
            name="type"
            required
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value as AccountType })}
          >
            <option value={AccountType.CHECKING}>Checking</option>
            <option value={AccountType.SAVINGS}>Savings</option>
            <option value={AccountType.CREDIT_CARD}>Credit Card</option>
            <option value={AccountType.LOAN}>Loan</option>
            <option value={AccountType.INVESTMENT}>Investment</option>
            <option value={AccountType.CASH}>Cash</option>
            <option value={AccountType.OTHER}>Other</option>
          </Select>
        </div>

        <div>
          <Input
            label="Currency"
            id="currency"
            name="currency"
            type="text"
            value={formData.currency}
            onChange={(e) => setFormData({ ...formData, currency: e.target.value.toUpperCase() })}
            placeholder="USD"
            maxLength={3}
          />
        </div>

        <div>
          <Input
            label="Institution"
            id="institution"
            name="institution"
            type="text"
            value={formData.institution}
            onChange={(e) => setFormData({ ...formData, institution: e.target.value })}
            placeholder="e.g., Chase, Bank of America"
          />
        </div>

        <div>
          <Input
            label="Account Number (Last 4 digits)"
            id="account_number"
            name="account_number"
            type="text"
            value={formData.account_number}
            onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
            placeholder="1234"
            maxLength={4}
          />
        </div>

        <div>
          <Input
            label="Opening Balance"
            id="opening_balance"
            name="opening_balance"
            type="number"
            required
            step="0.01"
            value={formData.opening_balance}
            onChange={(e) => setFormData({ ...formData, opening_balance: e.target.value })}
            placeholder="0.00"
            helperText="The starting balance for this account"
          />
        </div>

        <div>
          <Input
            label="Opening Balance Date"
            id="opening_balance_date"
            name="opening_balance_date"
            type="date"
            value={formData.opening_balance_date}
            onChange={(e) => setFormData({ ...formData, opening_balance_date: e.target.value })}
            helperText="Optional - date of the opening balance"
          />
        </div>

        {account && account.current_balance && (
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700">
              Calculated Balance
            </label>
            <div className="mt-1 text-lg font-semibold text-gray-900">
              ${parseFloat(account.current_balance).toFixed(2)}
            </div>
            <p className="mt-1 text-xs text-gray-500">
              This balance is calculated from your opening balance and all transactions
            </p>
          </div>
        )}

        <div className="sm:col-span-2">
          <Textarea
            label="Notes"
            id="notes"
            name="notes"
            rows={3}
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            placeholder="Optional notes about this account"
          />
        </div>

        <div className="sm:col-span-2">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
              Account is active
            </label>
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {loading ? "Saving..." : account ? "Update Account" : "Create Account"}
        </button>
      </div>
    </form>
  );
}
