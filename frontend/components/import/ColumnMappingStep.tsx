"use client";

import { useState } from "react";
import { CSVPreviewResponse, CSVColumnMapping } from "@/types";
import { Select } from "@/components/ui";

interface ColumnMappingStepProps {
  preview: CSVPreviewResponse;
  initialMapping: CSVColumnMapping;
  onComplete: (step: string, data: any) => void;
  onBack: () => void;
}

export default function ColumnMappingStep({
  preview,
  initialMapping,
  onComplete,
  onBack,
}: ColumnMappingStepProps) {
  const [mapping, setMapping] = useState<CSVColumnMapping>(initialMapping);

  const handleMappingChange = (field: keyof CSVColumnMapping, value: string) => {
    setMapping({ ...mapping, [field]: value });
  };

  const handleContinue = () => {
    // Validate required fields
    if (!mapping.date || !mapping.amount) {
      alert("Date and Amount columns are required");
      return;
    }

    onComplete("mapping", { mapping });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-text-primary mb-2">Step 2: Map CSV Columns</h2>
        <p className="text-sm text-text-secondary">
          {preview.detected_format && preview.detected_format !== "generic" ? (
            <span className="text-success-600 font-medium">
              Detected format: {preview.detected_format.toUpperCase()}
            </span>
          ) : (
            "Match your CSV columns to transaction fields"
          )}
        </p>
      </div>

      {/* Column Mapping Form */}
      <div className="space-y-4">
        {/* Date - Required */}
        <Select
          label="Date Column"
          id="date"
          name="date"
          value={mapping.date}
          onChange={(e) => handleMappingChange("date", e.target.value)}
          required
        >
          <option value="">Select column...</option>
          {preview.columns.map((col) => (
            <option key={col} value={col}>
              {col}
            </option>
          ))}
        </Select>

        {/* Amount - Required */}
        <Select
          label="Amount Column"
          id="amount"
          name="amount"
          value={mapping.amount}
          onChange={(e) => handleMappingChange("amount", e.target.value)}
          required
        >
          <option value="">Select column...</option>
          {preview.columns.map((col) => (
            <option key={col} value={col}>
              {col}
            </option>
          ))}
        </Select>

        {/* Description - Optional */}
        <Select
          label="Description Column (optional)"
          id="description"
          name="description"
          value={mapping.description || ""}
          onChange={(e) => handleMappingChange("description", e.target.value)}
        >
          <option value="">None</option>
          {preview.columns.map((col) => (
            <option key={col} value={col}>
              {col}
            </option>
          ))}
        </Select>

        {/* Payee - Optional */}
        <Select
          label="Payee Column (optional)"
          id="payee"
          name="payee"
          value={mapping.payee || ""}
          onChange={(e) => handleMappingChange("payee", e.target.value)}
        >
          <option value="">None</option>
          {preview.columns.map((col) => (
            <option key={col} value={col}>
              {col}
            </option>
          ))}
        </Select>
      </div>

      {/* Sample Data Preview */}
      <div>
        <h3 className="text-sm font-medium text-text-secondary mb-2">Sample Data Preview</h3>
        <div className="border border-border rounded-md overflow-x-auto">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-surface-secondary">
              <tr>
                {preview.columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-2 text-left text-xs font-medium text-text-tertiary uppercase"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-surface divide-y divide-border">
              {preview.sample_rows.slice(0, 3).map((row, idx) => (
                <tr key={idx}>
                  {preview.columns.map((col) => (
                    <td key={col} className="px-4 py-2 text-sm text-text-primary whitespace-nowrap">
                      {row[col] || "-"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-text-tertiary mt-2">
          Showing first 3 rows of {preview.row_count} total rows
        </p>
      </div>

      {/* Actions */}
      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-text-secondary hover:bg-surface-secondary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Back
        </button>
        <button
          onClick={handleContinue}
          className="px-4 py-2 bg-primary-600 text-text-inverse rounded-md text-sm font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Continue
        </button>
      </div>
    </div>
  );
}
