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
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Budget Name *
          </label>
          <input
            type="text"
            id="name"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Monthly Groceries"
          />
        </div>

        <div>
          <label htmlFor="category_id" className="block text-sm font-medium text-gray-700">
            Category *
          </label>
          <select
            id="category_id"
            required
            value={formData.category_id}
            onChange={(e) => setFormData({ ...formData, category_id: parseInt(e.target.value) })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={0}>Select a category</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">Only expense categories are shown</p>
        </div>

        <div>
          <label htmlFor="period" className="block text-sm font-medium text-gray-700">
            Period *
          </label>
          <select
            id="period"
            required
            value={formData.period}
            onChange={(e) => setFormData({ ...formData, period: e.target.value as BudgetPeriod })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={BudgetPeriod.WEEKLY}>Weekly</option>
            <option value={BudgetPeriod.MONTHLY}>Monthly</option>
            <option value={BudgetPeriod.QUARTERLY}>Quarterly</option>
            <option value={BudgetPeriod.YEARLY}>Yearly</option>
          </select>
        </div>

        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
            Budget Amount *
          </label>
          <input
            type="number"
            id="amount"
            required
            step="0.01"
            min="0.01"
            value={formData.amount}
            onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="0.00"
          />
        </div>

        <div>
          <label htmlFor="alert_threshold" className="block text-sm font-medium text-gray-700">
            Alert Threshold (%)
          </label>
          <input
            type="number"
            id="alert_threshold"
            step="1"
            min="0"
            max="100"
            value={formData.alert_threshold}
            onChange={(e) => setFormData({ ...formData, alert_threshold: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="90"
          />
          <p className="mt-1 text-xs text-gray-500">
            Get alerted when reaching this percentage
          </p>
        </div>

        <div>
          <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
            Start Date *
          </label>
          <input
            type="date"
            id="start_date"
            required
            value={formData.start_date}
            onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
            End Date (Optional)
          </label>
          <input
            type="date"
            id="end_date"
            value={formData.end_date}
            onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="mt-1 text-xs text-gray-500">
            Leave empty for ongoing budget
          </p>
        </div>

        <div className="sm:col-span-2">
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="alert_enabled"
                checked={formData.alert_enabled}
                onChange={(e) => setFormData({ ...formData, alert_enabled: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="alert_enabled" className="ml-2 block text-sm text-gray-900">
                Enable alerts when threshold is reached
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="rollover"
                checked={formData.rollover}
                onChange={(e) => setFormData({ ...formData, rollover: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="rollover" className="ml-2 block text-sm text-gray-900">
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
          className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {loading ? "Saving..." : budget ? "Update Budget" : "Create Budget"}
        </button>
      </div>
    </form>
  );
}
