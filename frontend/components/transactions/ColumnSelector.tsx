"use client";

import { useState, useRef, useEffect } from "react";

export interface ColumnConfig {
  id: string;
  label: string;
  required?: boolean;
}

interface ColumnSelectorProps {
  columns: ColumnConfig[];
  visibleColumns: string[];
  onColumnsChange: (visibleColumns: string[]) => void;
}

export default function ColumnSelector({
  columns,
  visibleColumns,
  onColumnsChange,
}: ColumnSelectorProps) {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showDropdown]);

  const handleToggleColumn = (columnId: string) => {
    const column = columns.find((c) => c.id === columnId);
    if (column?.required) return; // Don't allow toggling required columns

    if (visibleColumns.includes(columnId)) {
      onColumnsChange(visibleColumns.filter((id) => id !== columnId));
    } else {
      onColumnsChange([...visibleColumns, columnId]);
    }
  };

  return (
    <div ref={dropdownRef} className="relative inline-block">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="inline-flex items-center px-3 py-1.5 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        title="Configure columns"
      >
        <span className="mr-2">⚙️</span>
        Columns
      </button>

      {showDropdown && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg z-20 border border-gray-200">
          <div className="p-3">
            <div className="text-xs font-medium text-gray-700 mb-2">Show / Hide Columns</div>
            <div className="space-y-2">
              {columns.map((column) => (
                <label
                  key={column.id}
                  className={`flex items-center text-sm ${
                    column.required ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:bg-gray-50"
                  } p-1 rounded`}
                >
                  <input
                    type="checkbox"
                    checked={visibleColumns.includes(column.id)}
                    onChange={() => handleToggleColumn(column.id)}
                    disabled={column.required}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                  />
                  <span className="flex-1">{column.label}</span>
                  {column.required && <span className="text-xs text-gray-400">(required)</span>}
                </label>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
