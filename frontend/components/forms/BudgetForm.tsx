"use client";

import { useState, useEffect } from "react";
import { Budget, BudgetCreate, BudgetUpdate, BudgetPeriod, Category, CategoryType } from "@/types";
import { categoriesAPI } from "@/lib/api";
import { Input, Select } from "@/components/ui";

interface BudgetFormProps {
  budget?: Budget;
  onSubmit: (data: BudgetCreate | BudgetUpdate) => Promise<void>;
  onCancel: () => void;
}

export default function BudgetForm({ budget, onSubmit, onCancel }: BudgetFormProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [formData, setFormData] = useState({
    category_id: budget?.category_id || 0,
    name: budget?.name || "",
    amount: budget?.amount || "0.00",
    period: budget?.period || BudgetPeriod.MONTHLY,
    start_date: budget?.start_date || new Date().toISOString().split("T")[0],
    end_date: budget?.end_date || "",
    rollover: budget?.rollover || false,
    alert_enabled: budget?.alert_enabled !== undefined ? budget.alert_enabled : true,
    alert_threshold: budget?.alert_threshold || "90.0",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const cats = await categoriesAPI.getAll();
      // Filter to expense categories only for budgets
      const expenseCategories = cats.filter(c => c.type === CategoryType.EXPENSE);
      setCategories(expenseCategories);

      // Set default category if creating new budget
      if (!budget && expenseCategories.length > 0) {
        setFormData(prev => ({ ...prev, category_id: expenseCategories[0].id }));
      }
    } catch (err) {
      console.error("Failed to load categories:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        end_date: formData.end_date || undefined,
      };
      await onSubmit(submitData);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save budget");
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
        <div className="sm:col-span-2">
          <Input
            label="Budget Name"
            id="name"
            name="name"
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Monthly Groceries"
          />
        </div>

        <div>
          <Select
            label="Category"
            id="category_id"
            name="category_id"
            required
            value={formData.category_id}
            onChange={(e) => setFormData({ ...formData, category_id: parseInt(e.target.value) })}
            helperText="Only expense categories are shown"
          >
            <option value={0}>Select a category</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Select
            label="Period"
            id="period"
            name="period"
            required
            value={formData.period}
            onChange={(e) => setFormData({ ...formData, period: e.target.value as BudgetPeriod })}
          >
            <option value={BudgetPeriod.WEEKLY}>Weekly</option>
            <option value={BudgetPeriod.MONTHLY}>Monthly</option>
            <option value={BudgetPeriod.QUARTERLY}>Quarterly</option>
            <option value={BudgetPeriod.YEARLY}>Yearly</option>
          </Select>
        </div>

        <div>
          <Input
            label="Budget Amount"
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
          <Input
            label="Alert Threshold (%)"
            id="alert_threshold"
            name="alert_threshold"
            type="number"
            step="1"
            min="0"
            max="100"
            value={formData.alert_threshold}
            onChange={(e) => setFormData({ ...formData, alert_threshold: e.target.value })}
            placeholder="90"
            helperText="Get alerted when reaching this percentage"
          />
        </div>

        <div>
          <Input
            label="Start Date"
            id="start_date"
            name="start_date"
            type="date"
            required
            value={formData.start_date}
            onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
          />
        </div>

        <div>
          <Input
            label="End Date (Optional)"
            id="end_date"
            name="end_date"
            type="date"
            value={formData.end_date}
            onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
            helperText="Leave empty for ongoing budget"
          />
        </div>

        <div className="sm:col-span-2">
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="alert_enabled"
                checked={formData.alert_enabled}
                onChange={(e) => setFormData({ ...formData, alert_enabled: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-border rounded"
              />
              <label htmlFor="alert_enabled" className="ml-2 block text-sm text-text-primary">
                Enable alerts when threshold is reached
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="rollover"
                checked={formData.rollover}
                onChange={(e) => setFormData({ ...formData, rollover: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-border rounded"
              />
              <label htmlFor="rollover" className="ml-2 block text-sm text-text-primary">
                Roll over unused budget to next period
              </label>
            </div>
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
          {loading ? "Saving..." : budget ? "Update Budget" : "Create Budget"}
        </button>
      </div>
    </form>
  );
}
