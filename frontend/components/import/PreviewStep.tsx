"use client";

import { useState, useEffect } from "react";
import { CSVPreviewResponse, OFXPreviewResponse, CSVColumnMapping, PotentialDuplicate } from "@/types";
import { importsAPI } from "@/lib/api";

interface PreviewStepProps {
  file: File;
  fileType: "csv" | "ofx" | "qfx";
  accountId: number;
  csvPreview?: CSVPreviewResponse | null;
  ofxPreview?: OFXPreviewResponse | null;
  columnMapping?: CSVColumnMapping | null;
  onComplete: (step: string, data: any) => void;
  onBack: () => void;
  onError: (error: string) => void;
}

export default function PreviewStep({
  file,
  fileType,
  accountId,
  csvPreview,
  ofxPreview,
  columnMapping,
  onComplete,
  onBack,
  onError,
}: PreviewStepProps) {
  const [isChecking, setIsChecking] = useState(false);
  const [duplicates, setDuplicates] = useState<PotentialDuplicate[]>([]);
  const [error, setError] = useState<string | null>(null);

  const transactionCount = fileType === "csv"
    ? csvPreview?.row_count || 0
    : ofxPreview?.transaction_count || 0;

  const previewTransactions = fileType === "csv"
    ? csvPreview?.sample_rows.slice(0, 5) || []
    : ofxPreview?.sample_transactions.slice(0, 5) || [];

  // Check for duplicates on mount
  useEffect(() => {
    checkDuplicates();
  }, []);

  const checkDuplicates = async () => {
    setIsChecking(true);
    setError(null);

    try {
      let duplicateResponse;

      if (fileType === "csv" && columnMapping) {
        duplicateResponse = await importsAPI.detectCSVDuplicates(file, accountId, columnMapping);
      } else {
        duplicateResponse = await importsAPI.detectOFXDuplicates(file, accountId);
      }

      setDuplicates(duplicateResponse.duplicates);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to check for duplicates");
      console.error("Duplicate check error:", err);
    } finally {
      setIsChecking(false);
    }
  };

  const handleContinue = async () => {
    // Pass duplicates to next step
    onComplete("preview", { duplicates });
  };

  const formatAmount = (amount: string | number) => {
    const num = typeof amount === "string" ? parseFloat(amount) : amount;
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(Math.abs(num));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-2">
          {fileType === "csv" ? "Step 3: Review Transactions" : "Step 2: Review Transactions"}
        </h2>
        <p className="text-sm text-gray-600">
          Review the transactions before importing
        </p>
      </div>

      {/* Summary Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Import Summary</h3>
            <div className="mt-2 text-sm text-blue-700 space-y-1">
              <p>• File: {file.name}</p>
              <p>• Total transactions: {transactionCount}</p>
              {isChecking ? (
                <p className="text-gray-600">• Checking for duplicates...</p>
              ) : (
                <>
                  {duplicates.length > 0 && (
                    <p className="text-yellow-700 font-medium">
                      • Found {duplicates.length} potential duplicate{duplicates.length !== 1 ? "s" : ""}
                    </p>
                  )}
                  {duplicates.length === 0 && (
                    <p className="text-green-700 font-medium">• No duplicates found</p>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Sample Transactions Preview */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">Sample Transactions</h3>
        <div className="border border-gray-300 rounded-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Payee</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {previewTransactions.map((txn: any, idx: number) => {
                // Map fields based on file type
                let date, description, payee, amount;

                if (fileType === "csv" && columnMapping) {
                  date = txn[columnMapping.date];
                  description = columnMapping.description ? txn[columnMapping.description] : "";
                  payee = columnMapping.payee ? txn[columnMapping.payee] : "";

                  // Handle split withdrawal/deposit columns
                  if (columnMapping.amount.includes('|')) {
                    const [debitCol, creditCol] = columnMapping.amount.split('|');
                    const debitVal = txn[debitCol];
                    const creditVal = txn[creditCol];

                    // Parse and clean the values
                    const parseAmount = (val: any): number | null => {
                      if (!val || val === '' || String(val).toLowerCase() === 'nan') return null;
                      const cleaned = String(val).replace(/[$,\s]/g, '');
                      const num = parseFloat(cleaned);
                      return isNaN(num) ? null : num;
                    };

                    const debit = parseAmount(debitVal);
                    const credit = parseAmount(creditVal);

                    // Use whichever value is present
                    amount = debit !== null ? debit : (credit !== null ? credit : 0);
                  } else {
                    amount = txn[columnMapping.amount];
                  }
                } else {
                  // OFX format
                  date = txn.date;
                  description = txn.description || "";
                  payee = txn.payee || "";
                  amount = txn.amount;
                }

                return (
                  <tr key={idx}>
                    <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">{date}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{description || "-"}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{payee || "-"}</td>
                    <td className="px-4 py-2 text-sm text-gray-900 text-right whitespace-nowrap">
                      {formatAmount(amount)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Showing first {previewTransactions.length} of {transactionCount} transactions
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
          disabled={isChecking}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isChecking ? "Checking..." : "Continue"}
        </button>
      </div>
    </div>
  );
}
