"use client";

import { useState, useEffect } from "react";
import { Transaction, TransactionCreate, TransactionUpdate, TransactionType, Account, Category } from "@/types";
import { accountsAPI, categoriesAPI } from "@/lib/api";
import { Input, Select, Textarea } from "@/components/ui";
import { getErrorMessage } from "@/lib/utils/errors";

interface TransactionFormProps {
  transaction?: Transaction;
  onSubmit: (data: TransactionCreate | TransactionUpdate) => Promise<void>;
  onCancel: () => void;
}

export default function TransactionForm({ transaction, onSubmit, onCancel }: TransactionFormProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [formData, setFormData] = useState({
    account_id: transaction?.account_id || 0,
    category_id: transaction?.category_id || 0,
    type: transaction?.type || TransactionType.DEBIT,
    amount: transaction?.amount || "0.00",
    date: transaction?.date || new Date().toISOString().split("T")[0],
    description: transaction?.description || "",
    payee: transaction?.payee_name || transaction?.payee || "",
    notes: transaction?.notes || "",
    is_recurring: transaction?.is_recurring || false,
    tags: transaction?.tags || [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accts, cats] = await Promise.all([
        accountsAPI.getAll(),
        categoriesAPI.getAll(),
      ]);
      setAccounts(accts);
      setCategories(cats);

      // Set default account if creating new transaction
      if (!transaction && accts.length > 0) {
        setFormData(prev => ({ ...prev, account_id: accts[0].id }));
      }
    } catch (err) {
      console.error("Failed to load data:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const submitData: any = {
        ...formData,
        category_id: formData.category_id || undefined,
      };

      // Remove empty strings and convert to undefined (for proper JSON serialization)
      Object.keys(submitData).forEach((key) => {
        if (submitData[key] === "") {
          submitData[key] = undefined;
        }
      });

      await onSubmit(submitData);
    } catch (err: any) {
      setError(getErrorMessage(err, "Failed to save transaction"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="rounded-md bg-danger-50 p-4">
          <p className="text-sm text-danger-800">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <Select
            label="Transaction Type"
            id="type"
            name="type"
            required
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value as TransactionType })}
          >
            <option value={TransactionType.DEBIT}>📤 Expense</option>
            <option value={TransactionType.CREDIT}>📥 Income</option>
            <option value={TransactionType.TRANSFER}>🔄 Transfer</option>
          </Select>
        </div>

        <div>
          <Input
            label="Amount"
            id="amount"
            name="amount"
            type="number"
            required
            step="0.01"
            min="0.01"
            value={formData.amount}
            onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
            placeholder="0.00"
          />
        </div>

        <div>
          <Select
            label="Account"
            id="account_id"
            name="account_id"
            required
            value={formData.account_id}
            onChange={(e) => setFormData({ ...formData, account_id: parseInt(e.target.value) })}
          >
            <option value={0}>Select an account</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Select
            label="Category"
            id="category_id"
            name="category_id"
            value={formData.category_id}
            onChange={(e) => setFormData({ ...formData, category_id: parseInt(e.target.value) })}
          >
            <option value={0}>Uncategorized</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Input
            label="Date"
            id="date"
            name="date"
            type="date"
            required
            value={formData.date}
            onChange={(e) => setFormData({ ...formData, date: e.target.value })}
          />
        </div>

        <div>
          <Input
            label="Payee"
            id="payee"
            name="payee"
            type="text"
            value={formData.payee}
            onChange={(e) => setFormData({ ...formData, payee: e.target.value })}
            placeholder="e.g., Starbucks, Amazon"
          />
        </div>

        <div className="sm:col-span-2">
          <Input
            label="Description"
            id="description"
            name="description"
            type="text"
            required
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="e.g., Coffee at Starbucks"
          />
        </div>

        <div className="sm:col-span-2">
          <Textarea
            label="Notes"
            id="notes"
            name="notes"
            rows={3}
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            placeholder="Optional notes"
          />
        </div>

        <div className="sm:col-span-2">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_recurring"
              checked={formData.is_recurring}
              onChange={(e) => setFormData({ ...formData, is_recurring: e.target.checked })}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-border rounded"
            />
            <label htmlFor="is_recurring" className="ml-2 block text-sm text-text-primary">
              Recurring transaction
            </label>
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-border rounded-md shadow-sm text-sm font-medium text-text-secondary bg-surface hover:bg-surface-secondary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-text-inverse bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
        >
          {loading ? "Saving..." : transaction ? "Update Transaction" : "Create Transaction"}
        </button>
      </div>
    </form>
  );
}
