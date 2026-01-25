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
  width?: string;
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
  width,
}: ColumnFilterProps) {
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [textFilterValue, setTextFilterValue] = useState((currentFilter || "").toString());
  const [startDate, setStartDate] = useState(currentDateRange?.start || "");
  const [endDate, setEndDate] = useState(currentDateRange?.end || "");
  const [dropdownPosition, setDropdownPosition] = useState<"bottom" | "top">("bottom");
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

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

  // Adjust dropdown position based on available space
  useEffect(() => {
    if (showFilterDropdown && buttonRef.current) {
      const buttonRect = buttonRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const spaceBelow = viewportHeight - buttonRect.bottom;
      const dropdownHeight = 300; // Approximate max height

      if (spaceBelow < dropdownHeight && buttonRect.top > dropdownHeight) {
        setDropdownPosition("top");
      } else {
        setDropdownPosition("bottom");
      }
    }
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
      className={`px-6 py-3 ${alignmentClasses[align]} text-xs font-medium text-text-tertiary uppercase tracking-wider relative ${width || ""}`}
      style={width ? { maxWidth: width } : undefined}
    >
      <div className="flex items-center gap-2 justify-between">
        <span>{label}</span>

        <div className="flex items-center gap-1">
          {sortable && (
            <button
              onClick={handleSortClick}
              className={`text-xs hover:text-text-secondary transition-colors ${
                currentSort ? "text-primary-600" : "text-text-disabled"
              }`}
              title="Sort"
            >
              {getSortIcon()}
            </button>
          )}

          {filterable && (
            <div ref={dropdownRef} className="relative">
              <button
                ref={buttonRef}
                onClick={handleFilterClick}
                className={`text-xs hover:text-text-secondary transition-colors ${
                  currentFilter !== undefined && currentFilter !== "" ? "text-primary-600" : "text-text-disabled"
                }`}
                title="Filter"
              >
                🔍
              </button>

              {showFilterDropdown && (
                <div className={`fixed w-64 bg-surface rounded-md shadow-lg z-50 border border-border-light ${
                  dropdownPosition === "bottom" ? "mt-2" : "mb-2"
                }`}
                style={{
                  top: dropdownPosition === "bottom" && buttonRef.current
                    ? buttonRef.current.getBoundingClientRect().bottom + window.scrollY + 8
                    : undefined,
                  bottom: dropdownPosition === "top" && buttonRef.current
                    ? window.innerHeight - buttonRef.current.getBoundingClientRect().top - window.scrollY + 8
                    : undefined,
                  right: buttonRef.current
                    ? window.innerWidth - buttonRef.current.getBoundingClientRect().right
                    : undefined,
                }}
                >
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
                        className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        autoFocus
                      />
                      <div className="mt-2 flex gap-2">
                        <button
                          onClick={() => {
                            handleFilterSelect(textFilterValue || null);
                            setShowFilterDropdown(false);
                          }}
                          className="flex-1 px-3 py-1.5 text-xs bg-primary-600 text-white rounded hover:bg-primary-700"
                        >
                          Apply
                        </button>
                        <button
                          onClick={() => {
                            setTextFilterValue("");
                            handleFilterSelect(null);
                            setShowFilterDropdown(false);
                          }}
                          className="flex-1 px-3 py-1.5 text-xs bg-surface-tertiary text-text-secondary rounded hover:bg-border"
                        >
                          Clear
                        </button>
                      </div>
                    </div>
                  ) : filterType === "dateRange" ? (
                    <div className="p-3">
                      <div className="space-y-3">
                        <div>
                          <label className="block text-xs font-medium text-text-secondary mb-1">Start Date</label>
                          <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-text-secondary mb-1">End Date</label>
                          <input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
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
                          className="flex-1 px-3 py-1.5 text-xs bg-primary-600 text-white rounded hover:bg-primary-700"
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
                          className="flex-1 px-3 py-1.5 text-xs bg-surface-tertiary text-text-secondary rounded hover:bg-border"
                        >
                          Clear
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="py-1">
                      <button
                        onClick={() => handleFilterSelect(null)}
                        className="block w-full text-left px-4 py-2 text-sm text-text-secondary hover:bg-surface-secondary"
                      >
                        All
                      </button>
                      {filterOptions.map((option) => (
                        <button
                          key={option.value}
                          onClick={() => handleFilterSelect(option.value)}
                          className={`block w-full text-left px-4 py-2 text-sm hover:bg-surface-secondary ${
                            currentFilter === option.value
                              ? "bg-primary-50 text-primary-700 font-medium"
                              : "text-text-secondary"
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
