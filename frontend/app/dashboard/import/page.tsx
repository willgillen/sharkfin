"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import DashboardLayout from "@/components/layout/DashboardLayout";
import FileUploadStep from "@/components/import/FileUploadStep";
import ColumnMappingStep from "@/components/import/ColumnMappingStep";
import PreviewStep from "@/components/import/PreviewStep";
import SmartRuleSuggestionsStep from "@/components/import/SmartRuleSuggestionsStep";
import DuplicateReviewStep from "@/components/import/DuplicateReviewStep";
import ImportResultStep from "@/components/import/ImportResultStep";
import {
  CSVPreviewResponse,
  OFXPreviewResponse,
  CSVColumnMapping,
  PotentialDuplicate,
  ImportExecuteResponse,
  CategorizationRule
} from "@/types";

type ImportStep = "upload" | "mapping" | "preview" | "smart-suggestions" | "duplicates" | "result";

export default function ImportPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  // Wizard state
  const [currentStep, setCurrentStep] = useState<ImportStep>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<"csv" | "ofx" | "qfx" | null>(null);
  const [accountId, setAccountId] = useState<number>(0);

  // CSV-specific state
  const [csvPreview, setCsvPreview] = useState<CSVPreviewResponse | null>(null);
  const [columnMapping, setColumnMapping] = useState<CSVColumnMapping | null>(null);

  // OFX-specific state
  const [ofxPreview, setOfxPreview] = useState<OFXPreviewResponse | null>(null);

  // Duplicate detection state
  const [duplicates, setDuplicates] = useState<PotentialDuplicate[]>([]);
  const [skipRows, setSkipRows] = useState<number[]>([]);

  // Result state
  const [importResult, setImportResult] = useState<ImportExecuteResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  const handleStepComplete = (step: ImportStep, data?: any) => {
    setError("");

    switch (step) {
      case "upload":
        setFile(data.file);
        setFileType(data.fileType);
        setAccountId(data.accountId);

        if (data.fileType === "csv") {
          setCsvPreview(data.preview);
          setColumnMapping(data.preview.suggested_mapping);
          setCurrentStep("mapping");
        } else {
          setOfxPreview(data.preview);
          setCurrentStep("preview");
        }
        break;

      case "mapping":
        setColumnMapping(data.mapping);
        setCurrentStep("preview");
        break;

      case "preview":
        // After preview, go to smart suggestions
        setCurrentStep("smart-suggestions");
        break;

      case "smart-suggestions":
        // After smart suggestions, check for duplicates
        setDuplicates(data.duplicates);
        setSkipRows(data.skipRows || []);

        if (data.duplicates && data.duplicates.length > 0) {
          setCurrentStep("duplicates");
        } else {
          // No duplicates, go straight to import
          setImportResult(data.result);
          setCurrentStep("result");
        }
        break;

      case "duplicates":
        setSkipRows(data.skipRows);
        setImportResult(data.result);
        setCurrentStep("result");
        break;
    }
  };

  const handleBack = () => {
    setError("");

    switch (currentStep) {
      case "mapping":
        setCurrentStep("upload");
        break;
      case "preview":
        if (fileType === "csv") {
          setCurrentStep("mapping");
        } else {
          setCurrentStep("upload");
        }
        break;
      case "smart-suggestions":
        setCurrentStep("preview");
        break;
      case "duplicates":
        setCurrentStep("smart-suggestions");
        break;
      case "result":
        // Reset and start over
        setFile(null);
        setFileType(null);
        setCsvPreview(null);
        setOfxPreview(null);
        setColumnMapping(null);
        setDuplicates([]);
        setSkipRows([]);
        setImportResult(null);
        setCurrentStep("upload");
        break;
    }
  };

  const handleStartOver = () => {
    setFile(null);
    setFileType(null);
    setCsvPreview(null);
    setOfxPreview(null);
    setColumnMapping(null);
    setDuplicates([]);
    setSkipRows([]);
    setImportResult(null);
    setError("");
    setCurrentStep("upload");
  };

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0 max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Import Transactions</h1>
          <p className="mt-2 text-sm text-gray-600">
            Import transactions from CSV files or OFX/QFX (Quicken) bank downloads
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <nav aria-label="Progress">
            <ol className="flex items-center justify-between">
              {[
                { id: "upload", name: "Upload File" },
                { id: "mapping", name: fileType === "csv" ? "Map Columns" : "Preview", disabled: fileType !== "csv" },
                { id: "preview", name: "Review" },
                { id: "smart-suggestions", name: "Smart Rules" },
                { id: "duplicates", name: "Duplicates", disabled: duplicates.length === 0 },
                { id: "result", name: "Complete" },
              ].map((step, idx) => {
                const isCurrent = currentStep === step.id;
                const isComplete =
                  (step.id === "upload" && !["upload"].includes(currentStep)) ||
                  (step.id === "mapping" && ["preview", "smart-suggestions", "duplicates", "result"].includes(currentStep)) ||
                  (step.id === "preview" && ["smart-suggestions", "duplicates", "result"].includes(currentStep)) ||
                  (step.id === "smart-suggestions" && ["duplicates", "result"].includes(currentStep)) ||
                  (step.id === "duplicates" && currentStep === "result");

                if (step.disabled) return null;

                return (
                  <li key={step.id} className={`flex-1 ${idx > 0 ? "ml-8" : ""}`}>
                    <div className="flex items-center">
                      <div className="flex items-center">
                        <div
                          className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                            isComplete
                              ? "border-green-600 bg-green-600"
                              : isCurrent
                              ? "border-blue-600 bg-blue-600"
                              : "border-gray-300 bg-white"
                          }`}
                        >
                          {isComplete ? (
                            <svg className="h-6 w-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path
                                fillRule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clipRule="evenodd"
                              />
                            </svg>
                          ) : (
                            <span
                              className={`text-sm font-medium ${
                                isCurrent ? "text-white" : "text-gray-500"
                              }`}
                            >
                              {idx + 1}
                            </span>
                          )}
                        </div>
                        <span
                          className={`ml-3 text-sm font-medium ${
                            isCurrent ? "text-blue-600" : isComplete ? "text-green-600" : "text-gray-500"
                          }`}
                        >
                          {step.name}
                        </span>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ol>
          </nav>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step Content */}
        <div className="bg-white shadow rounded-lg p-6">
          {currentStep === "upload" && (
            <FileUploadStep onComplete={handleStepComplete} onError={setError} />
          )}

          {currentStep === "mapping" && csvPreview && columnMapping && (
            <ColumnMappingStep
              preview={csvPreview}
              initialMapping={columnMapping}
              onComplete={handleStepComplete}
              onBack={handleBack}
            />
          )}

          {currentStep === "preview" && (
            <PreviewStep
              file={file!}
              fileType={fileType!}
              accountId={accountId}
              csvPreview={csvPreview}
              ofxPreview={ofxPreview}
              columnMapping={columnMapping}
              onComplete={handleStepComplete}
              onBack={handleBack}
              onError={setError}
            />
          )}

          {currentStep === "smart-suggestions" && (
            <SmartRuleSuggestionsStep
              file={file!}
              fileType={fileType!}
              accountId={accountId}
              csvPreview={csvPreview}
              ofxPreview={ofxPreview}
              columnMapping={columnMapping}
              onComplete={handleStepComplete}
              onBack={handleBack}
              onError={setError}
            />
          )}

          {currentStep === "duplicates" && (
            <DuplicateReviewStep
              file={file!}
              fileType={fileType!}
              accountId={accountId}
              duplicates={duplicates}
              columnMapping={columnMapping}
              onComplete={handleStepComplete}
              onBack={handleBack}
              onError={setError}
            />
          )}

          {currentStep === "result" && importResult && (
            <ImportResultStep
              result={importResult}
              onStartOver={handleStartOver}
              onViewTransactions={() => router.push("/dashboard/transactions")}
            />
          )}
        </div>

        {/* View Import History Link */}
        <div className="mt-6 text-center">
          <button
            onClick={() => router.push("/dashboard/import/history")}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            View Import History
          </button>
        </div>
      </div>
    </DashboardLayout>
  );
}
