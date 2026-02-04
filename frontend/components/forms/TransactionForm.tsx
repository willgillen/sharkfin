"use client";

import { useState, useEffect } from "react";
import { Transaction, TransactionCreate, TransactionUpdate, TransactionType, Account, Category, PayeeWithCategory } from "@/types";
import { accountsAPI, categoriesAPI, payeesAPI } from "@/lib/api";
import { Input, Select, Textarea, PayeeAutocomplete } from "@/components/ui";
import { getErrorMessage } from "@/lib/utils/errors";

interface TransactionFormProps {
  transaction?: Transaction;
  onSubmit: (data: TransactionCreate) => Promise<void>;
  onCancel: () => void;
}

export default function TransactionForm({ transaction, onSubmit, onCancel }: TransactionFormProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedPayee, setSelectedPayee] = useState<PayeeWithCategory | null>(null);
  const [formData, setFormData] = useState({
    account_id: transaction?.account_id || 0,
    category_id: transaction?.category_id || 0,
    type: transaction?.type || TransactionType.DEBIT,
    amount: transaction?.amount || "0.00",
    date: transaction?.date || new Date().toISOString().split("T")[0],
    description: transaction?.description || "",
    payee_id: transaction?.payee_id || undefined as number | undefined,
    notes: transaction?.notes || "",
    is_recurring: transaction?.is_recurring || false,
    tags: transaction?.tags || [],
  });
  const [payeeInputValue, setPayeeInputValue] = useState(transaction?.payee_name || transaction?.payee || "");
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

      // Load existing payee if editing a transaction with a payee_id
      if (transaction?.payee_id) {
        try {
          const payee = await payeesAPI.getById(transaction.payee_id);
          setSelectedPayee({
            ...payee,
            default_category_name: null, // Will be populated if needed
          });
        } catch {
          // Payee may have been deleted, that's okay
        }
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
        payee_id: formData.payee_id || undefined,
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

  const handlePayeeSelect = (payee: PayeeWithCategory | null) => {
    setSelectedPayee(payee);
    setFormData(prev => ({
      ...prev,
      payee_id: payee?.id || undefined,
    }));
    if (payee) {
      setPayeeInputValue(payee.canonical_name);
      // If payee has a default category and no category is selected, use it
      if (payee.default_category_id && !formData.category_id) {
        setFormData(prev => ({
          ...prev,
          category_id: payee.default_category_id || 0,
        }));
      }
    } else {
      setPayeeInputValue("");
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
          <PayeeAutocomplete
            label="Payee"
            value={selectedPayee}
            inputValue={payeeInputValue}
            onSelect={handlePayeeSelect}
            onInputChange={setPayeeInputValue}
            placeholder="Search or create payee..."
            helperText="Select an existing payee or create a new one"
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
