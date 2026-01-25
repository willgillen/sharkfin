"use client";

import { useState, useCallback, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { accountsAPI, importsAPI } from "@/lib/api";
import { Account } from "@/types";
import { Select } from "@/components/ui";

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
        <p className="text-text-secondary">Loading accounts...</p>
      </div>
    );
  }

  if (accounts.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-text-secondary mb-4">No accounts found. Please create an account first.</p>
        <a href="/dashboard/accounts/new" className="text-primary-600 hover:text-primary-800">
          Create Account
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-text-primary mb-4">Step 1: Select Account & Upload File</h2>
        <p className="text-sm text-text-secondary mb-6">
          Choose which account these transactions belong to, then upload a CSV or OFX/QFX file.
        </p>
      </div>

      {/* Account Selection */}
      <div>
        <Select
          label="Import to Account"
          id="account"
          name="account"
          value={selectedAccountId}
          onChange={(e) => setSelectedAccountId(parseInt(e.target.value))}
          disabled={uploading}
        >
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({account.type})
            </option>
          ))}
        </Select>
      </div>

      {/* File Upload Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? "border-primary-500 bg-primary-50"
            : uploading
            ? "border-border bg-surface-secondary cursor-not-allowed"
            : "border-border hover:border-primary-400 hover:bg-surface-secondary"
        }`}
      >
        <input {...getInputProps()} />

        <div className="space-y-4">
          {uploading ? (
            <>
              <div className="mx-auto h-12 w-12 text-text-tertiary">
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
              <p className="text-sm text-text-secondary">Processing file...</p>
            </>
          ) : (
            <>
              <svg
                className="mx-auto h-12 w-12 text-text-tertiary"
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
                <p className="text-sm text-primary-600 font-medium">Drop file here...</p>
              ) : (
                <>
                  <p className="text-sm text-text-secondary">
                    <span className="font-medium text-primary-600 hover:text-primary-500">
                      Click to upload
                    </span>{" "}
                    or drag and drop
                  </p>
                  <p className="text-xs text-text-tertiary">CSV, OFX, or QFX files</p>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Supported Formats Info */}
      <div className="bg-primary-50 border border-primary-200 rounded-md p-4">
        <h3 className="text-sm font-medium text-primary-900 mb-2">Supported Formats</h3>
        <ul className="text-xs text-primary-800 space-y-1">
          <li>• <strong>CSV</strong> - Mint, Chase, Bank of America, Wells Fargo, or generic format</li>
          <li>• <strong>OFX/QFX</strong> - Quicken and most online banking downloads</li>
        </ul>
        <p className="text-xs text-primary-700 mt-2">
          The system will automatically detect your file format and suggest column mappings.
        </p>
      </div>
    </div>
  );
}
