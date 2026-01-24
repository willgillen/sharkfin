"use client";

import { useState, useEffect } from "react";
import { Category, CategoryCreate, CategoryUpdate, CategoryType } from "@/types";
import { categoriesAPI } from "@/lib/api";
import { Input, Select } from "@/components/ui";

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
        <div className="rounded-md bg-danger-50 p-4">
          <p className="text-sm text-danger-800">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Input
            label="Category Name"
            id="name"
            name="name"
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Groceries, Salary"
          />
        </div>

        <div>
          <Select
            label="Category Type"
            id="type"
            name="type"
            required
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value as CategoryType, parent_id: 0 })}
          >
            <option value={CategoryType.INCOME}>Income</option>
            <option value={CategoryType.EXPENSE}>Expense</option>
          </Select>
        </div>

        <div>
          <Select
            label="Parent Category (Optional)"
            id="parent_id"
            name="parent_id"
            value={formData.parent_id}
            onChange={(e) => setFormData({ ...formData, parent_id: parseInt(e.target.value) })}
            helperText="Create subcategories by selecting a parent"
          >
            <option value={0}>None (Top Level)</option>
            {availableParents.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="color" className="block text-sm font-medium text-text-secondary mb-1">
            Color
          </label>
          <div className="flex items-center space-x-2">
            <input
              type="color"
              id="color"
              value={formData.color}
              onChange={(e) => setFormData({ ...formData, color: e.target.value })}
              className="h-10 w-20 border border-border rounded cursor-pointer"
            />
            <Input
              type="text"
              value={formData.color}
              onChange={(e) => setFormData({ ...formData, color: e.target.value })}
              placeholder="#3b82f6"
              pattern="^#[0-9A-Fa-f]{6}$"
              helperText="Use hex color format (e.g., #3b82f6)"
            />
          </div>
        </div>

        <div>
          <Input
            label="Icon (Emoji)"
            id="icon"
            name="icon"
            type="text"
            value={formData.icon}
            onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
            placeholder="🛒"
            maxLength={2}
            helperText="Optional emoji to represent this category"
          />
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
          {loading ? "Saving..." : category ? "Update Category" : "Create Category"}
        </button>
      </div>
    </form>
  );
}
