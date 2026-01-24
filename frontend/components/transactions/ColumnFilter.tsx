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
  filterType?: "select" | "text" | "dateRange";
  currentFilter?: string | number;
  currentDateRange?: { start: string; end: string };
  currentSort?: SortOrder;
  onSort?: (order: SortOrder) => void;
  onFilter?: (value: string | number | null) => void;
  onDateRangeFilter?: (start: string | null, end: string | null) => void;
  align?: "left" | "center" | "right";
}

export default function ColumnFilter({
  label,
  sortable = false,
  filterable = false,
  filterOptions = [],
  filterType = "select",
  currentFilter,
  currentDateRange,
  currentSort,
  onSort,
  onFilter,
  onDateRangeFilter,
  align = "left",
}: ColumnFilterProps) {
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [textFilterValue, setTextFilterValue] = useState((currentFilter || "").toString());
  const [startDate, setStartDate] = useState(currentDateRange?.start || "");
  const [endDate, setEndDate] = useState(currentDateRange?.end || "");
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
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                  {filterType === "text" ? (
                    <div className="p-3">
                      <input
                        type="text"
                        value={textFilterValue}
                        onChange={(e) => setTextFilterValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            handleFilterSelect(textFilterValue || null);
                            setShowFilterDropdown(false);
                          }
                        }}
                        placeholder="Search..."
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        autoFocus
                      />
                      <div className="mt-2 flex gap-2">
                        <button
                          onClick={() => {
                            handleFilterSelect(textFilterValue || null);
                            setShowFilterDropdown(false);
                          }}
                          className="flex-1 px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Apply
                        </button>
                        <button
                          onClick={() => {
                            setTextFilterValue("");
                            handleFilterSelect(null);
                            setShowFilterDropdown(false);
                          }}
                          className="flex-1 px-3 py-1.5 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                        >
                          Clear
                        </button>
                      </div>
                    </div>
                  ) : filterType === "dateRange" ? (
                    <div className="p-3">
                      <div className="space-y-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Start Date</label>
                          <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">End Date</label>
                          <input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <button
                          onClick={() => {
                            if (onDateRangeFilter) {
                              onDateRangeFilter(startDate || null, endDate || null);
                            }
                            setShowFilterDropdown(false);
                          }}
                          className="flex-1 px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Apply
                        </button>
                        <button
                          onClick={() => {
                            setStartDate("");
                            setEndDate("");
                            if (onDateRangeFilter) {
                              onDateRangeFilter(null, null);
                            }
                            setShowFilterDropdown(false);
                          }}
                          className="flex-1 px-3 py-1.5 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                        >
                          Clear
                        </button>
                      </div>
                    </div>
                  ) : (
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
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </th>
  );
}
