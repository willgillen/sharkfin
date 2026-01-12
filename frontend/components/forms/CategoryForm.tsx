"use client";

import { useState, useEffect } from "react";
import { Category, CategoryCreate, CategoryUpdate, CategoryType } from "@/types";
import { categoriesAPI } from "@/lib/api";

interface CategoryFormProps {
  category?: Category;
  onSubmit: (data: CategoryCreate | CategoryUpdate) => Promise<void>;
  onCancel: () => void;
}

export default function CategoryForm({ category, onSubmit, onCancel }: CategoryFormProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [formData, setFormData] = useState({
    name: category?.name || "",
    type: category?.type || CategoryType.EXPENSE,
    color: category?.color || "#3b82f6",
    icon: category?.icon || "",
    parent_id: category?.parent_id || 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const cats = await categoriesAPI.getAll();
      // Filter out the current category if editing (can't be its own parent)
      const filteredCats = category
        ? cats.filter(c => c.id !== category.id)
        : cats;
      setCategories(filteredCats);
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
        parent_id: formData.parent_id || undefined,
        color: formData.color || undefined,
        icon: formData.icon || undefined,
      };
      await onSubmit(submitData);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save category");
    } finally {
      setLoading(false);
    }
  };

  // Filter parent categories by type (can only be parent of same type)
  const availableParents = categories.filter(c => c.type === formData.type && !c.parent_id);

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
            Category Name *
          </label>
          <input
            type="text"
            id="name"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Groceries, Salary"
          />
        </div>

        <div>
          <label htmlFor="type" className="block text-sm font-medium text-gray-700">
            Category Type *
          </label>
          <select
            id="type"
            required
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value as CategoryType, parent_id: 0 })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={CategoryType.INCOME}>Income</option>
            <option value={CategoryType.EXPENSE}>Expense</option>
          </select>
        </div>

        <div>
          <label htmlFor="parent_id" className="block text-sm font-medium text-gray-700">
            Parent Category (Optional)
          </label>
          <select
            id="parent_id"
            value={formData.parent_id}
            onChange={(e) => setFormData({ ...formData, parent_id: parseInt(e.target.value) })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={0}>None (Top Level)</option>
            {availableParents.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Create subcategories by selecting a parent
          </p>
        </div>

        <div>
          <label htmlFor="color" className="block text-sm font-medium text-gray-700">
            Color
          </label>
          <div className="mt-1 flex items-center space-x-2">
            <input
              type="color"
              id="color"
              value={formData.color}
              onChange={(e) => setFormData({ ...formData, color: e.target.value })}
              className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
            />
            <input
              type="text"
              value={formData.color}
              onChange={(e) => setFormData({ ...formData, color: e.target.value })}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="#3b82f6"
              pattern="^#[0-9A-Fa-f]{6}$"
            />
          </div>
          <p className="mt-1 text-xs text-gray-500">
            Use hex color format (e.g., #3b82f6)
          </p>
        </div>

        <div>
          <label htmlFor="icon" className="block text-sm font-medium text-gray-700">
            Icon (Emoji)
          </label>
          <input
            type="text"
            id="icon"
            value={formData.icon}
            onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="🛒"
            maxLength={2}
          />
          <p className="mt-1 text-xs text-gray-500">
            Optional emoji to represent this category
          </p>
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
          {loading ? "Saving..." : category ? "Update Category" : "Create Category"}
        </button>
      </div>
    </form>
  );
}
