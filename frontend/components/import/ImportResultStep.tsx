"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ImportExecuteResponse } from "@/types";
import { rulesAPI } from "@/lib/api";

interface ImportResultStepProps {
  result: ImportExecuteResponse;
  onStartOver: () => void;
  onViewTransactions: () => void;
}

export default function ImportResultStep({ result, onStartOver, onViewTransactions }: ImportResultStepProps) {
  const router = useRouter();
  const [applyingRules, setApplyingRules] = useState(false);
  const [rulesApplied, setRulesApplied] = useState(false);
  const [ruleStats, setRuleStats] = useState<{ categorized: number; rulesUsed: number } | null>(null);

  const hasErrors = result.error_count > 0;
  const hasSkipped = result.duplicate_count > 0;
  const isSuccess = result.imported_count > 0;

  const handleViewHistory = () => {
    router.push("/dashboard/import/history");
  };

  const handleApplyRules = async () => {
    try {
      setApplyingRules(true);
      // Apply rules to all uncategorized transactions
      const response = await rulesAPI.applyRules({
        overwrite_existing: false, // Only apply to uncategorized
      });
      setRuleStats({
        categorized: response.categorized_count,
        rulesUsed: response.rules_used,
      });
      setRulesApplied(true);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to apply rules");
    } finally {
      setApplyingRules(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        {isSuccess && !hasErrors && (
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-success-100 mb-4">
            <svg className="h-6 w-6 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}
        {hasErrors && (
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-warning-100 mb-4">
            <svg className="h-6 w-6 text-warning-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
        )}

        <h2 className="text-lg font-medium text-text-primary mb-2">
          {isSuccess && !hasErrors && "Import Complete!"}
          {hasErrors && "Import Completed with Warnings"}
          {!isSuccess && "Import Failed"}
        </h2>
        <p className="text-sm text-text-secondary">
          {isSuccess && !hasErrors && "Your transactions have been successfully imported."}
          {hasErrors && "Some transactions were imported, but there were issues with others."}
          {!isSuccess && "No transactions were imported. Please check your file and try again."}
        </p>
      </div>

      {/* Results Summary */}
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <dl className="grid grid-cols-1 gap-5 sm:grid-cols-3">
            {/* Imported */}
            <div className="bg-success-50 px-4 py-5 rounded-lg border border-success-200">
              <dt className="text-sm font-medium text-success-900 truncate">Imported</dt>
              <dd className="mt-1 text-3xl font-semibold text-success-600">{result.imported_count}</dd>
              <p className="mt-1 text-xs text-success-700">Successfully added</p>
            </div>

            {/* Skipped */}
            <div className="bg-warning-50 px-4 py-5 rounded-lg border border-warning-200">
              <dt className="text-sm font-medium text-warning-900 truncate">Skipped</dt>
              <dd className="mt-1 text-3xl font-semibold text-warning-600">{result.duplicate_count}</dd>
              <p className="mt-1 text-xs text-warning-700">Duplicates avoided</p>
            </div>

            {/* Errors */}
            <div className={`px-4 py-5 rounded-lg border ${hasErrors ? "bg-danger-50 border-danger-200" : "bg-surface-secondary border-border"}`}>
              <dt className={`text-sm font-medium truncate ${hasErrors ? "text-danger-900" : "text-text-primary"}`}>Errors</dt>
              <dd className={`mt-1 text-3xl font-semibold ${hasErrors ? "text-danger-600" : "text-text-secondary"}`}>{result.error_count}</dd>
              <p className={`mt-1 text-xs ${hasErrors ? "text-danger-700" : "text-text-secondary"}`}>Failed to import</p>
            </div>
          </dl>
        </div>
      </div>

      {/* Import Details */}
      <div className="bg-surface-secondary border border-border rounded-lg p-4">
        <h3 className="text-sm font-medium text-text-primary mb-2">Import Details</h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-text-secondary">Import ID:</dt>
            <dd className="text-text-primary font-medium">#{result.import_id}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-text-secondary">Total Rows:</dt>
            <dd className="text-text-primary">{result.total_rows}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-text-secondary">Status:</dt>
            <dd>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                result.status === "completed" ? "bg-success-100 text-success-800" : "bg-warning-100 text-warning-800"
              }`}>
                {result.status}
              </span>
            </dd>
          </div>
        </dl>
      </div>

      {/* Error Messages */}
      {hasErrors && result.errors && result.errors.length > 0 && (
        <div className="bg-danger-50 border border-danger-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-danger-900 mb-2">Error Details</h3>
          <ul className="space-y-1 text-sm text-danger-700">
            {result.errors.slice(0, 5).map((error, idx) => (
              <li key={idx} className="flex items-start">
                <span className="mr-2">•</span>
                <span>{error}</span>
              </li>
            ))}
            {result.errors.length > 5 && (
              <li className="text-xs text-danger-600 italic mt-2">
                ... and {result.errors.length - 5} more error{result.errors.length - 5 !== 1 ? "s" : ""}
              </li>
            )}
          </ul>
        </div>
      )}

      {/* Help Text */}
      {hasSkipped && (
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-primary-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-primary-700">
                {result.duplicate_count} transaction{result.duplicate_count !== 1 ? "s were" : " was"} skipped because {result.duplicate_count !== 1 ? "they" : "it"} appeared to be duplicate{result.duplicate_count !== 1 ? "s" : ""}.
                You can view your import history to see all skipped transactions.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Auto-Categorization */}
      {isSuccess && !rulesApplied && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z"/>
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-purple-900">Auto-Categorize with Rules</h3>
                <p className="mt-1 text-sm text-purple-700">
                  Apply your categorization rules to automatically categorize the imported transactions.
                </p>
              </div>
            </div>
            <button
              onClick={handleApplyRules}
              disabled={applyingRules}
              className="ml-4 px-4 py-2 bg-purple-600 text-white rounded-md text-sm font-medium hover:bg-purple-700 disabled:opacity-50 whitespace-nowrap"
            >
              {applyingRules ? "Applying..." : "Apply Rules"}
            </button>
          </div>
        </div>
      )}

      {/* Rules Applied Success */}
      {rulesApplied && ruleStats && (
        <div className="bg-success-50 border border-success-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-success-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-success-900">Rules Applied Successfully!</h3>
              <p className="mt-1 text-sm text-success-700">
                Categorized {ruleStats.categorized} transaction{ruleStats.categorized !== 1 ? "s" : ""} using {ruleStats.rulesUsed} rule{ruleStats.rulesUsed !== 1 ? "s" : ""}.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={onViewTransactions}
          className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700"
        >
          View Transactions
        </button>
        <button
          onClick={handleViewHistory}
          className="flex-1 px-4 py-2 border border-border rounded-md text-sm font-medium text-text-secondary hover:bg-surface-secondary"
        >
          View Import History
        </button>
        <button
          onClick={onStartOver}
          className="flex-1 px-4 py-2 border border-border rounded-md text-sm font-medium text-text-secondary hover:bg-surface-secondary"
        >
          Import Another File
        </button>
      </div>
    </div>
  );
}
