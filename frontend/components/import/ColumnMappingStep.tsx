"use client";

import { useState } from "react";
import { CSVPreviewResponse, CSVColumnMapping } from "@/types";

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
        <h2 className="text-lg font-medium text-gray-900 mb-2">Step 2: Map CSV Columns</h2>
        <p className="text-sm text-gray-600">
          {preview.detected_format && preview.detected_format !== "generic" ? (
            <span className="text-green-600 font-medium">
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
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Date Column <span className="text-red-500">*</span>
          </label>
          <select
            value={mapping.date}
            onChange={(e) => handleMappingChange("date", e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md"
            required
          >
            <option value="">Select column...</option>
            {preview.columns.map((col) => (
              <option key={col} value={col}>
                {col}
              </option>
            ))}
          </select>
        </div>

        {/* Amount - Required */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Amount Column <span className="text-red-500">*</span>
          </label>
          <select
            value={mapping.amount}
            onChange={(e) => handleMappingChange("amount", e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md"
            required
          >
            <option value="">Select column...</option>
            {preview.columns.map((col) => (
              <option key={col} value={col}>
                {col}
              </option>
            ))}
          </select>
        </div>

        {/* Description - Optional */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description Column <span className="text-gray-400">(optional)</span>
          </label>
          <select
            value={mapping.description || ""}
            onChange={(e) => handleMappingChange("description", e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">None</option>
            {preview.columns.map((col) => (
              <option key={col} value={col}>
                {col}
              </option>
            ))}
          </select>
        </div>

        {/* Payee - Optional */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Payee Column <span className="text-gray-400">(optional)</span>
          </label>
          <select
            value={mapping.payee || ""}
            onChange={(e) => handleMappingChange("payee", e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">None</option>
            {preview.columns.map((col) => (
              <option key={col} value={col}>
                {col}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Sample Data Preview */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">Sample Data Preview</h3>
        <div className="border border-gray-300 rounded-md overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {preview.columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {preview.sample_rows.slice(0, 3).map((row, idx) => (
                <tr key={idx}>
                  {preview.columns.map((col) => (
                    <td key={col} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                      {row[col] || "-"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Showing first 3 rows of {preview.row_count} total rows
        </p>
      </div>

      {/* Actions */}
      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={handleContinue}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
        >
          Continue
        </button>
      </div>
    </div>
  );
}
