"use client";

import { useRouter } from "next/navigation";
import { ImportExecuteResponse } from "@/types";

interface ImportResultStepProps {
  result: ImportExecuteResponse;
  onStartOver: () => void;
  onViewTransactions: () => void;
}

export default function ImportResultStep({ result, onStartOver, onViewTransactions }: ImportResultStepProps) {
  const router = useRouter();

  const hasErrors = result.error_count > 0;
  const hasSkipped = result.duplicate_count > 0;
  const isSuccess = result.imported_count > 0;

  const handleViewHistory = () => {
    router.push("/dashboard/import/history");
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        {isSuccess && !hasErrors && (
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
            <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}
        {hasErrors && (
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 mb-4">
            <svg className="h-6 w-6 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
        )}

        <h2 className="text-lg font-medium text-gray-900 mb-2">
          {isSuccess && !hasErrors && "Import Complete!"}
          {hasErrors && "Import Completed with Warnings"}
          {!isSuccess && "Import Failed"}
        </h2>
        <p className="text-sm text-gray-600">
          {isSuccess && !hasErrors && "Your transactions have been successfully imported."}
          {hasErrors && "Some transactions were imported, but there were issues with others."}
          {!isSuccess && "No transactions were imported. Please check your file and try again."}
        </p>
      </div>

      {/* Results Summary */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <dl className="grid grid-cols-1 gap-5 sm:grid-cols-3">
            {/* Imported */}
            <div className="bg-green-50 px-4 py-5 rounded-lg border border-green-200">
              <dt className="text-sm font-medium text-green-900 truncate">Imported</dt>
              <dd className="mt-1 text-3xl font-semibold text-green-600">{result.imported_count}</dd>
              <p className="mt-1 text-xs text-green-700">Successfully added</p>
            </div>

            {/* Skipped */}
            <div className="bg-yellow-50 px-4 py-5 rounded-lg border border-yellow-200">
              <dt className="text-sm font-medium text-yellow-900 truncate">Skipped</dt>
              <dd className="mt-1 text-3xl font-semibold text-yellow-600">{result.duplicate_count}</dd>
              <p className="mt-1 text-xs text-yellow-700">Duplicates avoided</p>
            </div>

            {/* Errors */}
            <div className={`px-4 py-5 rounded-lg border ${hasErrors ? "bg-red-50 border-red-200" : "bg-gray-50 border-gray-200"}`}>
              <dt className={`text-sm font-medium truncate ${hasErrors ? "text-red-900" : "text-gray-900"}`}>Errors</dt>
              <dd className={`mt-1 text-3xl font-semibold ${hasErrors ? "text-red-600" : "text-gray-600"}`}>{result.error_count}</dd>
              <p className={`mt-1 text-xs ${hasErrors ? "text-red-700" : "text-gray-700"}`}>Failed to import</p>
            </div>
          </dl>
        </div>
      </div>

      {/* Import Details */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Import Details</h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-600">Import ID:</dt>
            <dd className="text-gray-900 font-medium">#{result.import_id}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Total Rows:</dt>
            <dd className="text-gray-900">{result.total_rows}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Status:</dt>
            <dd>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                result.status === "completed" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
              }`}>
                {result.status}
              </span>
            </dd>
          </div>
        </dl>
      </div>

      {/* Error Messages */}
      {hasErrors && result.errors && result.errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-red-900 mb-2">Error Details</h3>
          <ul className="space-y-1 text-sm text-red-700">
            {result.errors.slice(0, 5).map((error, idx) => (
              <li key={idx} className="flex items-start">
                <span className="mr-2">•</span>
                <span>{error}</span>
              </li>
            ))}
            {result.errors.length > 5 && (
              <li className="text-xs text-red-600 italic mt-2">
                ... and {result.errors.length - 5} more error{result.errors.length - 5 !== 1 ? "s" : ""}
              </li>
            )}
          </ul>
        </div>
      )}

      {/* Help Text */}
      {hasSkipped && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                {result.duplicate_count} transaction{result.duplicate_count !== 1 ? "s were" : " was"} skipped because {result.duplicate_count !== 1 ? "they" : "it"} appeared to be duplicate{result.duplicate_count !== 1 ? "s" : ""}.
                You can view your import history to see all skipped transactions.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={onViewTransactions}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
        >
          View Transactions
        </button>
        <button
          onClick={handleViewHistory}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          View Import History
        </button>
        <button
          onClick={onStartOver}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Import Another File
        </button>
      </div>
    </div>
  );
}
