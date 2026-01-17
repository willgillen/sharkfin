"use client";

import { useState } from "react";
import { PotentialDuplicate, CSVColumnMapping } from "@/types";
import { importsAPI } from "@/lib/api";

interface DuplicateReviewStepProps {
  file: File;
  fileType: "csv" | "ofx" | "qfx";
  accountId: number;
  duplicates: PotentialDuplicate[];
  columnMapping?: CSVColumnMapping | null;
  onComplete: (step: string, data: any) => void;
  onBack: () => void;
  onError: (error: string) => void;
}

export default function DuplicateReviewStep({
  file,
  fileType,
  accountId,
  duplicates,
  columnMapping,
  onComplete,
  onBack,
  onError,
}: DuplicateReviewStepProps) {
  const [selectedSkips, setSelectedSkips] = useState<Set<number>>(
    new Set(duplicates.map((d) => d.new_transaction.row))
  );

  const toggleSkip = (rowNumber: number) => {
    const newSkips = new Set(selectedSkips);
    if (newSkips.has(rowNumber)) {
      newSkips.delete(rowNumber);
    } else {
      newSkips.add(rowNumber);
    }
    setSelectedSkips(newSkips);
  };

  const handleContinue = async () => {
    // Pass skip rows to next step (smart suggestions)
    const skipRows = Array.from(selectedSkips);
    onComplete("duplicates", { skipRows });
  };

  const formatAmount = (amount: string | number) => {
    const num = typeof amount === "string" ? parseFloat(amount) : amount;
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(Math.abs(num));
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.9) return "text-red-600 bg-red-50";
    if (score >= 0.8) return "text-orange-600 bg-orange-50";
    return "text-yellow-600 bg-yellow-50";
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.9) return "Very High";
    if (score >= 0.8) return "High";
    return "Medium";
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-2">
          {fileType === "csv" ? "Step 4: Review Duplicates" : "Step 3: Review Duplicates"}
        </h2>
        <p className="text-sm text-gray-600">
          We found {duplicates.length} potential duplicate transaction{duplicates.length !== 1 ? "s" : ""}.
          Review and select which ones to skip.
        </p>
      </div>

      {/* Selection Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-blue-900">
              {selectedSkips.size} transaction{selectedSkips.size !== 1 ? "s" : ""} will be skipped
            </p>
            <p className="text-xs text-blue-700 mt-1">
              {duplicates.length - selectedSkips.size} new transaction{duplicates.length - selectedSkips.size !== 1 ? "s" : ""} will be imported
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setSelectedSkips(new Set(duplicates.map((d) => d.new_transaction.row)))}
              className="text-xs text-blue-600 hover:text-blue-800 underline"
            >
              Skip All
            </button>
            <span className="text-gray-300">|</span>
            <button
              onClick={() => setSelectedSkips(new Set())}
              className="text-xs text-blue-600 hover:text-blue-800 underline"
            >
              Import All
            </button>
          </div>
        </div>
      </div>

      {/* Duplicates List */}
      <div className="space-y-4">
        {duplicates.map((duplicate, idx) => {
          const isSkipped = selectedSkips.has(duplicate.new_transaction.row);
          const newTxn = duplicate.new_transaction;

          return (
            <div
              key={idx}
              className={`border rounded-lg p-4 ${isSkipped ? "bg-gray-50 border-gray-300" : "bg-white border-blue-200"}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={isSkipped}
                    onChange={() => toggleSkip(newTxn.row)}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-900">
                    Skip this transaction
                  </span>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getConfidenceColor(duplicate.confidence_score)}`}>
                  {getConfidenceLabel(duplicate.confidence_score)} ({Math.round(duplicate.confidence_score * 100)}%)
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Existing Transaction */}
                <div className="border-r border-gray-200 pr-4">
                  <p className="text-xs font-medium text-gray-500 uppercase mb-2">Existing Transaction</p>
                  <div className="space-y-1 text-sm">
                    <p><span className="text-gray-600">Date:</span> {duplicate.existing_date}</p>
                    <p><span className="text-gray-600">Amount:</span> {formatAmount(duplicate.existing_amount)}</p>
                    <p><span className="text-gray-600">Description:</span> {duplicate.existing_description || "-"}</p>
                  </div>
                </div>

                {/* New Transaction */}
                <div className="pl-4">
                  <p className="text-xs font-medium text-gray-500 uppercase mb-2">New Transaction</p>
                  <div className="space-y-1 text-sm">
                    <p><span className="text-gray-600">Date:</span> {newTxn.date}</p>
                    <p><span className="text-gray-600">Amount:</span> {formatAmount(newTxn.amount)}</p>
                    <p><span className="text-gray-600">Description:</span> {newTxn.description || newTxn.payee || "-"}</p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
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
          Continue with {duplicates.length - selectedSkips.size} Transaction{duplicates.length - selectedSkips.size !== 1 ? "s" : ""}
        </button>
      </div>
    </div>
  );
}
