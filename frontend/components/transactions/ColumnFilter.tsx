"use client";

import { useState, useRef, useEffect } from "react";

export type SortOrder = "asc" | "desc" | null;

export interface FilterOption {
  label: string;
  value: string | number;
}

interface ColumnFilterProps {
  label: string;
  sortable?: boolean;
  filterable?: boolean;
  filterOptions?: FilterOption[];
  currentFilter?: string | number;
  currentSort?: SortOrder;
  onSort?: (order: SortOrder) => void;
  onFilter?: (value: string | number | null) => void;
  align?: "left" | "center" | "right";
}

export default function ColumnFilter({
  label,
  sortable = false,
  filterable = false,
  filterOptions = [],
  currentFilter,
  currentSort,
  onSort,
  onFilter,
  align = "left",
}: ColumnFilterProps) {
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowFilterDropdown(false);
      }
    };

    if (showFilterDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showFilterDropdown]);

  const handleSortClick = () => {
    if (!sortable || !onSort) return;

    if (currentSort === null) {
      onSort("desc");
    } else if (currentSort === "desc") {
      onSort("asc");
    } else {
      onSort(null);
    }
  };

  const handleFilterClick = () => {
    if (!filterable) return;
    setShowFilterDropdown(!showFilterDropdown);
  };

  const handleFilterSelect = (value: string | number | null) => {
    if (onFilter) {
      onFilter(value);
    }
    setShowFilterDropdown(false);
  };

  const alignmentClasses = {
    left: "text-left",
    center: "text-center",
    right: "text-right",
  };

  const getSortIcon = () => {
    if (currentSort === "asc") return "↑";
    if (currentSort === "desc") return "↓";
    return "⇅";
  };

  return (
    <th
      className={`px-6 py-3 ${alignmentClasses[align]} text-xs font-medium text-gray-500 uppercase tracking-wider relative`}
    >
      <div className="flex items-center gap-2 justify-between">
        <span>{label}</span>

        <div className="flex items-center gap-1">
          {sortable && (
            <button
              onClick={handleSortClick}
              className={`text-xs hover:text-gray-700 transition-colors ${
                currentSort ? "text-blue-600" : "text-gray-400"
              }`}
              title="Sort"
            >
              {getSortIcon()}
            </button>
          )}

          {filterable && (
            <div ref={dropdownRef} className="relative">
              <button
                onClick={handleFilterClick}
                className={`text-xs hover:text-gray-700 transition-colors ${
                  currentFilter !== undefined && currentFilter !== "" ? "text-blue-600" : "text-gray-400"
                }`}
                title="Filter"
              >
                🔍
              </button>

              {showFilterDropdown && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                  <div className="py-1">
                    <button
                      onClick={() => handleFilterSelect(null)}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      All
                    </button>
                    {filterOptions.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => handleFilterSelect(option.value)}
                        className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${
                          currentFilter === option.value
                            ? "bg-blue-50 text-blue-700 font-medium"
                            : "text-gray-700"
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </th>
  );
}
