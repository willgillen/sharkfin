"use client";

import { useState, useEffect } from "react";
import { CSVColumnMapping } from "@/types";
import { importsAPI } from "@/lib/api";

interface PayeeMapping {
  suggested: string;              // Extracted/suggested payee name
  final: string;                  // User's final choice (editable)
  transactionCount: number;       // Number of transactions using this payee
  sampleDescriptions: string[];   // Sample original descriptions
  avgConfidence: number;          // Average extraction confidence
}

interface PayeeReviewStepProps {
  file: File;
  fileType: "csv" | "ofx" | "qfx";
  accountId: number;
  columnMapping?: CSVColumnMapping | null;
  csvPreview?: any;
  ofxPreview?: any;
  skipRows?: number[];
  onComplete: (step: string, data: any) => void;
  onBack: () => void;
  onError: (error: string) => void;
}

export default function PayeeReviewStep({
  file,
  fileType,
  accountId,
  columnMapping,
  csvPreview,
  ofxPreview,
  skipRows = [],
  onComplete,
  onBack,
  onError,
}: PayeeReviewStepProps) {
  const [analyzing, setAnalyzing] = useState(true);
  const [payeeMappings, setPayeeMappings] = useState<PayeeMapping[]>([]);

  useEffect(() => {
    analyzePayees();
  }, []);

  const analyzePayees = async () => {
    setAnalyzing(true);

    try {
      // Call the new backend endpoints that analyze ALL transactions from the file
      let data;

      if (fileType === "csv" && columnMapping) {
        // Use CSV-specific endpoint that re-parses the full file
        data = await importsAPI.analyzeAllCSVPayees(file, columnMapping);
      } else if (fileType === "ofx" || fileType === "qfx") {
        // Use OFX-specific endpoint that re-parses the full file
        data = await importsAPI.analyzeAllOFXPayees(file);
      } else {
        throw new Error("Unsupported file type");
      }

      // Group by suggested payee name
      const payeeGroups = new Map<string, {
        descriptions: string[];
        confidences: number[];
      }>();

      data.payees.forEach((item: any) => {
        const existing = payeeGroups.get(item.suggested);
        if (existing) {
          existing.descriptions.push(item.original);
          existing.confidences.push(item.confidence);
        } else {
          payeeGroups.set(item.suggested, {
            descriptions: [item.original],
            confidences: [item.confidence]
          });
        }
      });

      // Create grouped payee mappings
      const mappings: PayeeMapping[] = Array.from(payeeGroups.entries()).map(([suggested, group]) => ({
        suggested,
        final: suggested, // Start with suggested name (user can edit)
        transactionCount: group.descriptions.length,
        sampleDescriptions: group.descriptions.slice(0, 3), // Show up to 3 samples
        avgConfidence: group.confidences.reduce((sum, c) => sum + c, 0) / group.confidences.length,
      }));

      // Sort by transaction count (most common first)
      mappings.sort((a, b) => b.transactionCount - a.transactionCount);

      setPayeeMappings(mappings);

    } catch (err: any) {
      console.error("Payee analysis error:", err);
      onError(err.message || "Failed to analyze payees");
    } finally {
      setAnalyzing(false);
    }
  };


  const handleContinue = () => {
    // Create a mapping from suggested names to final names
    // Only include overrides where user changed the name
    const payeeNameOverrides: Record<string, string> = {};

    payeeMappings.forEach((mapping) => {
      if (mapping.suggested !== mapping.final) {
        // User edited this payee name
        payeeNameOverrides[mapping.suggested] = mapping.final;
      }
    });

    onComplete("payee-review", {
      payeeNameOverrides,
    });
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-success-100 text-success-800">Very High</span>;
    } else if (confidence >= 0.8) {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-success-100 text-success-700">High</span>;
    } else if (confidence >= 0.7) {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-warning-100 text-warning-800">Medium</span>;
    } else {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-surface-tertiary text-text-primary">Low</span>;
    }
  };

  if (analyzing) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-medium text-text-primary mb-2">Analyzing Payees</h2>
          <p className="text-sm text-text-secondary">
            Extracting and analyzing payee information from transactions...
          </p>
        </div>

        <div className="flex justify-center items-center py-12">
          <div className="text-center">
            <svg className="animate-spin h-10 w-10 text-primary-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-sm text-text-secondary">Analyzing payees...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-text-primary mb-2">Review Payees</h2>
        <p className="text-sm text-text-secondary">
          Review and edit the {payeeMappings.length} unique payee{payeeMappings.length !== 1 ? 's' : ''} that will be created from this import.
          Edit payee names directly in the table or press Enter to save, Escape to cancel.
        </p>
      </div>

      {payeeMappings.length === 0 ? (
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-6 text-center">
          <svg className="mx-auto h-12 w-12 text-primary-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-sm font-medium text-primary-900 mb-1">No Payees Found</h3>
          <p className="text-sm text-primary-700">
            No payee information could be extracted from this import.
          </p>
        </div>
      ) : (
        <>
          {/* Info Box */}
          <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-primary-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-primary-900">Review Before Creating</h3>
                <p className="mt-1 text-sm text-primary-700">
                  These unique payees will be created in your account. Transactions with the same extracted payee name have been grouped together.
                  Review the names and edit any that need adjustment - your changes will apply to all grouped transactions.
                </p>
              </div>
            </div>
          </div>

          {/* Payee List */}
          <div className="bg-surface shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-border-light">
              <thead className="bg-surface-secondary">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider w-12">
                    #
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Payee Name (Editable)
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Sample Transactions
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider w-24 text-center">
                    Count
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider w-24">
                    Quality
                  </th>
                </tr>
              </thead>
              <tbody className="bg-surface divide-y divide-border-light">
                {payeeMappings.map((mapping, index) => (
                  <tr key={index} className="hover:bg-surface-secondary">
                    {/* Row Number */}
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-text-tertiary">
                      {index + 1}
                    </td>

                    {/* Editable Payee Name */}
                    <td className="px-4 py-3">
                      <input
                        type="text"
                        value={mapping.final}
                        onChange={(e) => {
                          const updated = [...payeeMappings];
                          updated[index].final = e.target.value;
                          setPayeeMappings(updated);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.currentTarget.blur();
                          } else if (e.key === "Escape") {
                            // Reset to suggested value
                            const updated = [...payeeMappings];
                            updated[index].final = updated[index].suggested;
                            setPayeeMappings(updated);
                            e.currentTarget.blur();
                          }
                        }}
                        className="w-full px-3 py-2 text-sm border border-border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Enter payee name"
                      />
                      {mapping.suggested !== mapping.final && (
                        <p className="mt-1 text-xs text-primary-600">
                          Changed from: {mapping.suggested}
                        </p>
                      )}
                    </td>

                    {/* Sample Descriptions */}
                    <td className="px-4 py-3">
                      <div className="space-y-1">
                        {mapping.sampleDescriptions.map((desc, i) => (
                          <div key={i} className="text-sm text-text-secondary line-clamp-1">
                            {desc}
                          </div>
                        ))}
                        {mapping.transactionCount > mapping.sampleDescriptions.length && (
                          <div className="text-xs text-text-tertiary italic">
                            +{mapping.transactionCount - mapping.sampleDescriptions.length} more...
                          </div>
                        )}
                      </div>
                    </td>

                    {/* Transaction Count */}
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                        {mapping.transactionCount}
                      </span>
                    </td>

                    {/* Quality Badge */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      {getConfidenceBadge(mapping.avgConfidence)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-text-secondary hover:bg-surface-secondary"
        >
          Back
        </button>
        <button
          onClick={handleContinue}
          className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700"
        >
          Continue to Import
        </button>
      </div>
    </div>
  );
}
