"use client";

import { useState, useEffect } from "react";
import { importsAPI } from "@/lib/api/imports";
import { CSVColumnMapping } from "@/types";
import {
  IntelligentPayeeAnalysisResponse,
  PayeeAssignment,
  TransactionPayeeAnalysis,
  PayeeAssignmentDecision,
} from "@/types/intelligent-matching";

interface EnhancedPayeeReviewStepProps {
  file: File;
  fileType: "csv" | "ofx" | "qfx";
  accountId: number;
  columnMapping?: CSVColumnMapping;
  skipRows?: number[];
  onComplete: (step: string, data: PayeeAssignmentDecision[]) => void;
  onBack: () => void;
  onError: (error: string) => void;
}

export default function EnhancedPayeeReviewStep({
  file,
  fileType,
  accountId,
  columnMapping,
  skipRows = [],
  onComplete,
  onBack,
  onError,
}: EnhancedPayeeReviewStepProps) {
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState<IntelligentPayeeAnalysisResponse | null>(null);
  const [assignments, setAssignments] = useState<Map<number, PayeeAssignment>>(new Map());

  // Collapsible sections state
  const [highConfidenceExpanded, setHighConfidenceExpanded] = useState(false);
  const [lowConfidenceExpanded, setLowConfidenceExpanded] = useState(true);
  const [newPayeesExpanded, setNewPayeesExpanded] = useState(true);

  // Load intelligent analysis on mount
  useEffect(() => {
    loadAnalysis();
  }, [file, fileType]);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      let result: IntelligentPayeeAnalysisResponse;

      if (fileType === "csv") {
        if (!columnMapping) {
          throw new Error("Column mapping required for CSV");
        }
        result = await importsAPI.analyzeCSVPayeesIntelligent(file, columnMapping);
      } else {
        result = await importsAPI.analyzeOFXPayeesIntelligent(file);
      }

      setAnalysis(result);

      // Initialize assignments from analysis
      const initialAssignments = new Map<number, PayeeAssignment>();
      result.analyses.forEach((a: TransactionPayeeAnalysis) => {
        if (!skipRows.includes(a.transaction_index)) {
          initialAssignments.set(a.transaction_index, {
            transactionIndex: a.transaction_index,
            originalDescription: a.original_description,
            extractedName: a.extracted_payee_name,
            matchType: a.match_type,
            matchedPayeeId: a.matched_payee_id ?? undefined,
            matchedPayeeName: a.matched_payee_name ?? undefined,
            matchConfidence: a.match_confidence,
            matchReason: a.match_reason,
            // For HIGH/LOW confidence: preselect matched payee
            selectedPayeeId: a.matched_payee_id ?? null,
            // For NO_MATCH: use extracted name as default new payee
            selectedNewPayeeName: a.match_type === "NO_MATCH" ? a.extracted_payee_name : "",
            alternativeMatches: a.alternative_matches,
          });
        }
      });

      setAssignments(initialAssignments);
    } catch (error: any) {
      console.error("Failed to analyze payees:", error);
      onError(error.response?.data?.detail || error.message || "Failed to analyze payees");
    } finally {
      setLoading(false);
    }
  };

  const handlePayeeSelect = (transactionIndex: number, payeeId: number | null) => {
    const assignment = assignments.get(transactionIndex);
    if (!assignment) return;

    setAssignments(
      new Map(
        assignments.set(transactionIndex, {
          ...assignment,
          selectedPayeeId: payeeId,
          selectedNewPayeeName: "", // Clear new payee name if selecting existing
        })
      )
    );
  };

  const handleNewPayeeNameChange = (transactionIndex: number, name: string) => {
    const assignment = assignments.get(transactionIndex);
    if (!assignment) return;

    setAssignments(
      new Map(
        assignments.set(transactionIndex, {
          ...assignment,
          selectedNewPayeeName: name,
          selectedPayeeId: null, // Clear selected payee if entering new name
        })
      )
    );
  };

  // Handle switching to "create new payee" mode for a transaction
  const handleCreateNewPayee = (transactionIndex: number) => {
    const assignment = assignments.get(transactionIndex);
    if (!assignment) return;

    setAssignments(
      new Map(
        assignments.set(transactionIndex, {
          ...assignment,
          selectedPayeeId: null,
          selectedNewPayeeName: assignment.extractedName, // Start with extracted name
          // Keep original matchType so we can restore it if user cancels
        })
      )
    );
  };

  // Handle canceling "create new" and returning to suggested match
  const handleCancelCreateNew = (transactionIndex: number) => {
    const assignment = assignments.get(transactionIndex);
    if (!assignment) return;

    setAssignments(
      new Map(
        assignments.set(transactionIndex, {
          ...assignment,
          selectedPayeeId: assignment.matchedPayeeId ?? null,
          selectedNewPayeeName: "",
        })
      )
    );
  };

  const handleGroupedPayeeNameChange = (transactionIndices: number[], name: string) => {
    // Update all transactions in this group with the new payee name
    const updatedAssignments = new Map(assignments);

    transactionIndices.forEach((txIndex) => {
      const assignment = updatedAssignments.get(txIndex);
      if (assignment) {
        updatedAssignments.set(txIndex, {
          ...assignment,
          selectedNewPayeeName: name,
          selectedPayeeId: null,
        });
      }
    });

    setAssignments(updatedAssignments);
  };

  const handleContinue = () => {
    // Build payee decisions from user's selections
    const decisions: PayeeAssignmentDecision[] = [];

    assignments.forEach((assignment) => {
      const decision: PayeeAssignmentDecision = {
        transaction_index: assignment.transactionIndex,
        original_description: assignment.originalDescription,
        create_pattern: true, // Always create patterns for learning
      };

      if (assignment.selectedPayeeId) {
        // User selected existing payee
        decision.payee_id = assignment.selectedPayeeId;
      } else if (assignment.selectedNewPayeeName?.trim()) {
        // User wants to create new payee
        decision.new_payee_name = assignment.selectedNewPayeeName.trim();
      } else if (assignment.matchType !== "NO_MATCH" && assignment.matchedPayeeId) {
        // Fallback: use matched payee if no explicit selection
        decision.payee_id = assignment.matchedPayeeId;
      } else {
        // Last resort: use extracted name
        decision.new_payee_name = assignment.extractedName;
      }

      decisions.push(decision);
    });

    onComplete("payee-review", decisions);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">Analyzing payees with intelligent matching...</p>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <p className="text-sm text-red-800">Failed to load payee analysis. Please try again.</p>
      </div>
    );
  }

  // Group assignments by match type
  const highConfidenceAssignments = Array.from(assignments.values()).filter(
    (a) => a.matchType === "HIGH_CONFIDENCE"
  );
  const lowConfidenceAssignments = Array.from(assignments.values()).filter(
    (a) => a.matchType === "LOW_CONFIDENCE"
  );
  const newPayeeAssignments = Array.from(assignments.values()).filter(
    (a) => a.matchType === "NO_MATCH"
  );

  // Group new payees by extracted name (like old PayeeReviewStep)
  interface PayeeGroup {
    suggestedName: string;
    transactionIndices: number[];
    sampleDescriptions: string[];
    transactionCount: number;
  }

  const payeeGroups = new Map<string, PayeeGroup>();

  newPayeeAssignments.forEach((assignment) => {
    const suggestedName = assignment.extractedName || "";
    if (!suggestedName) return; // Skip if no suggested name

    const existing = payeeGroups.get(suggestedName);

    if (existing) {
      existing.transactionIndices.push(assignment.transactionIndex);
      existing.sampleDescriptions.push(assignment.originalDescription);
      existing.transactionCount++;
    } else {
      payeeGroups.set(suggestedName, {
        suggestedName,
        transactionIndices: [assignment.transactionIndex],
        sampleDescriptions: [assignment.originalDescription],
        transactionCount: 1,
      });
    }
  });

  // Sort groups by transaction count (most common first)
  const sortedPayeeGroups = Array.from(payeeGroups.values()).sort(
    (a, b) => b.transactionCount - a.transactionCount
  );

  // Helper function to get the current edited name for a group
  const getGroupFinalName = (group: PayeeGroup): string => {
    // Get the selectedNewPayeeName from the first transaction in the group
    // (all transactions in a group should have the same edited name)
    const firstAssignment = assignments.get(group.transactionIndices[0]);
    return firstAssignment?.selectedNewPayeeName || group.suggestedName;
  };

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900">Intelligent Payee Matching Results</h3>
        <p className="mt-2 text-sm text-gray-600">
          We analyzed {analysis.summary.total_transactions} transactions and matched them to your existing payees.
        </p>

        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-3xl font-bold text-green-600">
              {analysis.summary.high_confidence_matches}
            </div>
            <div className="text-sm text-gray-600">High Confidence</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="text-3xl font-bold text-yellow-600">
              {analysis.summary.low_confidence_matches}
            </div>
            <div className="text-sm text-gray-600">Review Recommended</div>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-3xl font-bold text-blue-600">
              {analysis.summary.new_payees_needed}
            </div>
            <div className="text-sm text-gray-600">New Payees</div>
          </div>
        </div>
      </div>

      {/* HIGH CONFIDENCE SECTION */}
      {highConfidenceAssignments.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg">
          <div
            className="flex items-center justify-between p-4 cursor-pointer"
            onClick={() => setHighConfidenceExpanded(!highConfidenceExpanded)}
          >
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
              </svg>
              <h3 className="font-medium text-green-900">
                High Confidence Matches ({highConfidenceAssignments.length})
              </h3>
            </div>
            <svg
              className={`h-5 w-5 text-green-600 transform transition-transform ${highConfidenceExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>

          {highConfidenceExpanded && (
            <div className="p-4 space-y-3 border-t border-green-200">
              {highConfidenceAssignments.map((assignment) => {
                // Check if user has switched to "create new" mode for this item
                const isCreatingNew = assignment.selectedPayeeId === null && assignment.selectedNewPayeeName !== "";

                return (
                  <div key={assignment.transactionIndex} className="grid grid-cols-2 gap-4 p-3 bg-white rounded border">
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Transaction</label>
                      <p className="text-sm truncate" title={assignment.originalDescription}>
                        {assignment.originalDescription}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {assignment.matchReason} • {Math.round((assignment.matchConfidence || 0) * 100)}% confident
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Matched Payee</label>
                      {isCreatingNew ? (
                        // Show text input for new payee name
                        <div className="space-y-2">
                          <input
                            type="text"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            value={assignment.selectedNewPayeeName}
                            onChange={(e) => handleNewPayeeNameChange(assignment.transactionIndex, e.target.value)}
                            placeholder="Enter new payee name"
                          />
                          <button
                            type="button"
                            className="text-xs text-blue-600 hover:text-blue-800"
                            onClick={() => handleCancelCreateNew(assignment.transactionIndex)}
                          >
                            ← Back to suggestions
                          </button>
                        </div>
                      ) : (
                        // Show dropdown with suggestions + create new option
                        <select
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          value={assignment.selectedPayeeId?.toString() || ""}
                          onChange={(e) => {
                            if (e.target.value === "__create_new__") {
                              handleCreateNewPayee(assignment.transactionIndex);
                            } else {
                              handlePayeeSelect(assignment.transactionIndex, e.target.value ? Number(e.target.value) : null);
                            }
                          }}
                        >
                          <option value={assignment.matchedPayeeId?.toString()}>
                            {assignment.matchedPayeeName} (Suggested)
                          </option>
                          {assignment.alternativeMatches.map((alt) => (
                            <option key={alt.payee_id} value={alt.payee_id.toString()}>
                              {alt.payee_name} ({Math.round(alt.confidence * 100)}%)
                            </option>
                          ))}
                          <option value="__create_new__" className="font-medium">
                            ➕ Create New Payee...
                          </option>
                        </select>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* LOW CONFIDENCE SECTION */}
      {lowConfidenceAssignments.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg">
          <div
            className="flex items-center justify-between p-4 cursor-pointer"
            onClick={() => setLowConfidenceExpanded(!lowConfidenceExpanded)}
          >
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
              </svg>
              <h3 className="font-medium text-yellow-900">
                Review Recommended ({lowConfidenceAssignments.length})
              </h3>
            </div>
            <svg
              className={`h-5 w-5 text-yellow-600 transform transition-transform ${lowConfidenceExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>

          {lowConfidenceExpanded && (
            <div className="p-4 space-y-3 border-t border-yellow-200">
              {lowConfidenceAssignments.map((assignment) => {
                // Check if user has switched to "create new" mode for this item
                const isCreatingNew = assignment.selectedPayeeId === null && assignment.selectedNewPayeeName !== "";

                return (
                  <div key={assignment.transactionIndex} className="grid grid-cols-2 gap-4 p-3 bg-white rounded border">
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Transaction</label>
                      <p className="text-sm truncate" title={assignment.originalDescription}>
                        {assignment.originalDescription}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {assignment.matchReason} • {Math.round((assignment.matchConfidence || 0) * 100)}% confident
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Matched Payee</label>
                      {isCreatingNew ? (
                        // Show text input for new payee name
                        <div className="space-y-2">
                          <input
                            type="text"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            value={assignment.selectedNewPayeeName}
                            onChange={(e) => handleNewPayeeNameChange(assignment.transactionIndex, e.target.value)}
                            placeholder="Enter new payee name"
                          />
                          <button
                            type="button"
                            className="text-xs text-blue-600 hover:text-blue-800"
                            onClick={() => handleCancelCreateNew(assignment.transactionIndex)}
                          >
                            ← Back to suggestions
                          </button>
                        </div>
                      ) : (
                        // Show dropdown with suggestions + create new option
                        <select
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          value={assignment.selectedPayeeId?.toString() || ""}
                          onChange={(e) => {
                            if (e.target.value === "__create_new__") {
                              handleCreateNewPayee(assignment.transactionIndex);
                            } else {
                              handlePayeeSelect(assignment.transactionIndex, e.target.value ? Number(e.target.value) : null);
                            }
                          }}
                        >
                          <option value={assignment.matchedPayeeId?.toString()}>
                            {assignment.matchedPayeeName} (Suggested)
                          </option>
                          {assignment.alternativeMatches.map((alt) => (
                            <option key={alt.payee_id} value={alt.payee_id.toString()}>
                              {alt.payee_name} ({Math.round(alt.confidence * 100)}%)
                            </option>
                          ))}
                          <option value="__create_new__" className="font-medium">
                            ➕ Create New Payee...
                          </option>
                        </select>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* NEW PAYEES SECTION - GROUPED */}
      {sortedPayeeGroups.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg">
          <div
            className="flex items-center justify-between p-4 cursor-pointer"
            onClick={() => setNewPayeesExpanded(!newPayeesExpanded)}
          >
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
              </svg>
              <h3 className="font-medium text-blue-900">
                New Payees ({sortedPayeeGroups.length})
              </h3>
            </div>
            <svg
              className={`h-5 w-5 text-blue-600 transform transition-transform ${newPayeesExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>

          {newPayeesExpanded && (
            <div className="p-4 space-y-3 border-t border-blue-200">
              {sortedPayeeGroups.map((group, idx) => (
                <div key={`${group.suggestedName}-${idx}`} className="p-4 bg-white rounded border">
                  <div className="grid grid-cols-2 gap-4 mb-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">
                        Suggested Payee Name ({group.transactionCount} transaction{group.transactionCount > 1 ? 's' : ''})
                      </label>
                      <p className="text-sm font-medium text-gray-900">{group.suggestedName}</p>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">
                        Final Payee Name (editable)
                      </label>
                      <input
                        type="text"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={getGroupFinalName(group)}
                        onChange={(e) => handleGroupedPayeeNameChange(group.transactionIndices, e.target.value)}
                        placeholder="Enter payee name"
                      />
                    </div>
                  </div>

                  {/* Show sample transaction descriptions */}
                  <div className="mt-2 pt-2 border-t border-gray-100">
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      Sample Transactions:
                    </label>
                    <ul className="space-y-1">
                      {group.sampleDescriptions.slice(0, 3).map((desc, descIdx) => (
                        <li key={descIdx} className="text-xs text-gray-600 truncate" title={desc}>
                          • {desc}
                        </li>
                      ))}
                      {group.transactionCount > 3 && (
                        <li className="text-xs text-gray-500 italic">
                          ... and {group.transactionCount - 3} more
                        </li>
                      )}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-6">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={handleContinue}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
        >
          Continue to Import
        </button>
      </div>
    </div>
  );
}
