"use client";

import { useState, useCallback, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { accountsAPI, importsAPI } from "@/lib/api";
import { Account } from "@/types";

interface FileUploadStepProps {
  onComplete: (step: string, data: any) => void;
  onError: (error: string) => void;
}

export default function FileUploadStep({ onComplete, onError }: FileUploadStepProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<number>(0);
  const [uploading, setUploading] = useState(false);
  const [loadingAccounts, setLoadingAccounts] = useState(true);

  // Load accounts on mount
  useEffect(() => {
    const loadAccounts = async () => {
      try {
        const data = await accountsAPI.getAll();
        setAccounts(data);
        if (data.length > 0) {
          setSelectedAccountId(data[0].id);
        }
      } catch (err) {
        onError("Failed to load accounts");
      } finally {
        setLoadingAccounts(false);
      }
    };

    loadAccounts();
  }, [onError]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      const fileExtension = file.name.split(".").pop()?.toLowerCase();

      if (!["csv", "ofx", "qfx"].includes(fileExtension || "")) {
        onError("Invalid file type. Please upload a CSV, OFX, or QFX file.");
        return;
      }

      if (selectedAccountId === 0) {
        onError("Please select an account first.");
        return;
      }

      setUploading(true);
      onError("");

      try {
        let preview;
        const fileType = fileExtension as "csv" | "ofx" | "qfx";

        if (fileType === "csv") {
          preview = await importsAPI.previewCSV(file);
        } else {
          preview = await importsAPI.previewOFX(file);
        }

        onComplete("upload", {
          file,
          fileType,
          accountId: selectedAccountId,
          preview,
        });
      } catch (err: any) {
        onError(err.response?.data?.detail || "Failed to process file");
      } finally {
        setUploading(false);
      }
    },
    [selectedAccountId, onComplete, onError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/x-ofx": [".ofx"],
      "application/vnd.intu.qfx": [".qfx"],
    },
    multiple: false,
    disabled: uploading || selectedAccountId === 0,
  });

  if (loadingAccounts) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Loading accounts...</p>
      </div>
    );
  }

  if (accounts.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 mb-4">No accounts found. Please create an account first.</p>
        <a href="/dashboard/accounts/new" className="text-blue-600 hover:text-blue-800">
          Create Account
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Step 1: Select Account & Upload File</h2>
        <p className="text-sm text-gray-600 mb-6">
          Choose which account these transactions belong to, then upload a CSV or OFX/QFX file.
        </p>
      </div>

      {/* Account Selection */}
      <div>
        <label htmlFor="account" className="block text-sm font-medium text-gray-700 mb-2">
          Import to Account
        </label>
        <select
          id="account"
          value={selectedAccountId}
          onChange={(e) => setSelectedAccountId(parseInt(e.target.value))}
          className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          disabled={uploading}
        >
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({account.type})
            </option>
          ))}
        </select>
      </div>

      {/* File Upload Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? "border-blue-500 bg-blue-50"
            : uploading
            ? "border-gray-300 bg-gray-50 cursor-not-allowed"
            : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
        }`}
      >
        <input {...getInputProps()} />

        <div className="space-y-4">
          {uploading ? (
            <>
              <div className="mx-auto h-12 w-12 text-gray-400">
                <svg className="animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              </div>
              <p className="text-sm text-gray-600">Processing file...</p>
            </>
          ) : (
            <>
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>

              {isDragActive ? (
                <p className="text-sm text-blue-600 font-medium">Drop file here...</p>
              ) : (
                <>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium text-blue-600 hover:text-blue-500">
                      Click to upload
                    </span>{" "}
                    or drag and drop
                  </p>
                  <p className="text-xs text-gray-500">CSV, OFX, or QFX files</p>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Supported Formats Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">Supported Formats</h3>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• <strong>CSV</strong> - Mint, Chase, Bank of America, Wells Fargo, or generic format</li>
          <li>• <strong>OFX/QFX</strong> - Quicken and most online banking downloads</li>
        </ul>
        <p className="text-xs text-blue-700 mt-2">
          The system will automatically detect your file format and suggest column mappings.
        </p>
      </div>
    </div>
  );
}
