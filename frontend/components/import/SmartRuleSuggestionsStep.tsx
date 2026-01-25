"use client";

import { useState, useEffect } from "react";
import {
  SmartRuleSuggestionResponse,
  AnalyzeImportForRulesRequest,
  AnalyzeImportForRulesResponse,
  CSVColumnMapping,
  CategorizationRule
} from "@/types";
import { PayeeAssignmentDecision } from "@/types/intelligent-matching";
import { importsAPI, rulesAPI } from "@/lib/api";

interface SmartRuleSuggestionsStepProps {
  file: File;
  fileType: "csv" | "ofx" | "qfx";
  accountId: number;
  columnMapping?: CSVColumnMapping | null;
  csvPreview?: any;
  ofxPreview?: any;
  skipRows?: number[];
  payeeDecisions?: PayeeAssignmentDecision[];
  onComplete: (step: string, data: any) => void;
  onBack: () => void;
  onError: (error: string) => void;
}

export default function SmartRuleSuggestionsStep({
  file,
  fileType,
  accountId,
  columnMapping,
  csvPreview,
  ofxPreview,
  skipRows = [],
  payeeDecisions = [],
  onComplete,
  onBack,
  onError,
}: SmartRuleSuggestionsStepProps) {
  const [analyzing, setAnalyzing] = useState(true);
  const [suggestions, setSuggestions] = useState<SmartRuleSuggestionResponse[]>([]);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(new Set());
  const [creatingRules, setCreatingRules] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalyzeImportForRulesResponse | null>(null);

  useEffect(() => {
    analyzeTransactions();
  }, []);

  const analyzeTransactions = async () => {
    setAnalyzing(true);

    try {
      // Parse transactions from preview data
      const transactions = parseTransactionsForAnalysis();

      if (transactions.length === 0) {
        // No transactions to analyze, skip this step
        onComplete("smart-suggestions", { suggestionsCreated: [] });
        return;
      }

      // Call the smart analysis API
      const request: AnalyzeImportForRulesRequest = {
        transactions,
        min_occurrences: 2,  // Suggest if pattern appears 2+ times
        min_confidence: 0.6, // 60% confidence threshold
      };

      const result = await importsAPI.analyzeForRules(request);
      setAnalysisResult(result);
      setSuggestions(result.suggestions);

      // Auto-select high-confidence suggestions (>= 0.8)
      const autoSelect = new Set<number>();
      result.suggestions.forEach((suggestion, idx) => {
        if (suggestion.confidence >= 0.8) {
          autoSelect.add(idx);
        }
      });
      setSelectedSuggestions(autoSelect);

    } catch (err: any) {
      console.error("Smart rule analysis error:", err);
      onError(err.response?.data?.detail || "Failed to analyze transactions for rule suggestions");
      // Don't block the flow, just continue
      onComplete("smart-suggestions", { suggestionsCreated: [] });
    } finally {
      setAnalyzing(false);
    }
  };

  const parseTransactionsForAnalysis = (): Array<Record<string, any>> => {
    const transactions: Array<Record<string, any>> = [];

    if (fileType === "csv" && csvPreview && columnMapping) {
      // Parse CSV rows
      csvPreview.sample_rows.forEach((row: any) => {
        const date = row[columnMapping.date];
        let amount;

        // Handle split withdrawal/deposit columns
        if (columnMapping.amount.includes('|')) {
          const [debitCol, creditCol] = columnMapping.amount.split('|');
          const debitVal = row[debitCol];
          const creditVal = row[creditCol];

          const parseAmount = (val: any): number | null => {
            if (!val || val === '' || String(val).toLowerCase() === 'nan') return null;
            const cleaned = String(val).replace(/[$,\s]/g, '');
            const num = parseFloat(cleaned);
            return isNaN(num) ? null : num;
          };

          const debit = parseAmount(debitVal);
          const credit = parseAmount(creditVal);
          amount = debit !== null ? debit : (credit !== null ? credit : 0);
        } else {
          amount = row[columnMapping.amount];
        }

        const description = columnMapping.description ? row[columnMapping.description] : "";
        const payee = columnMapping.payee ? row[columnMapping.payee] : "";

        transactions.push({
          date,
          amount: typeof amount === 'string' ? parseFloat(amount) : amount,
          description,
          payee,
        });
      });
    } else if ((fileType === "ofx" || fileType === "qfx") && ofxPreview) {
      // Parse OFX transactions
      ofxPreview.sample_transactions.forEach((txn: any) => {
        transactions.push({
          date: txn.date,
          amount: txn.amount,
          description: txn.description || "",
          payee: txn.payee || "",
        });
      });
    }

    return transactions;
  };

  const toggleSuggestion = (index: number) => {
    const newSelected = new Set(selectedSuggestions);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedSuggestions(newSelected);
  };

  const handleContinue = async () => {
    setCreatingRules(true);

    try {
      const createdRules: CategorizationRule[] = [];

      // Create rules for selected suggestions
      if (selectedSuggestions.size > 0) {
        for (const index of Array.from(selectedSuggestions)) {
          const suggestion = suggestions[index];

          const ruleData = {
            name: suggestion.suggested_name,
            priority: 100, // Default priority
            enabled: true,
            payee_pattern: suggestion.payee_pattern,
            payee_match_type: suggestion.payee_match_type,
            description_pattern: undefined,
            description_match_type: undefined,
            amount_min: undefined,
            amount_max: undefined,
            transaction_type: undefined,
            category_id: undefined, // User will need to set this manually
            new_payee: suggestion.detected_merchant || undefined,
            notes_append: undefined,
          };

          const createdRule = await rulesAPI.create(ruleData);
          createdRules.push(createdRule);
        }
      }

      // Execute import with intelligent payee decisions
      let result;
      const importRequest = {
        account_id: accountId,
        skip_rows: skipRows,
        payee_assignments: payeeDecisions,
      };

      if (fileType === "csv" && columnMapping) {
        result = await importsAPI.executeCSVImportWithDecisions(file, columnMapping, importRequest);
      } else {
        result = await importsAPI.executeOFXImportWithDecisions(file, importRequest);
      }

      onComplete("smart-suggestions", {
        suggestionsCreated: createdRules,
        result
      });

    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || "Failed to process import";
      onError(errorMsg);
    } finally {
      setCreatingRules(false);
    }
  };

  const handleSkip = () => {
    // Still need to check for duplicates even if skipping rule creation
    handleContinue();
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
          <h2 className="text-lg font-medium text-text-primary mb-2">Analyzing Transactions</h2>
          <p className="text-sm text-text-secondary">
            Looking for patterns to suggest smart categorization rules...
          </p>
        </div>

        <div className="flex justify-center items-center py-12">
          <div className="text-center">
            <svg className="animate-spin h-10 w-10 text-primary-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-sm text-text-secondary">Analyzing transaction patterns...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-text-primary mb-2">Smart Rule Suggestions</h2>
        <p className="text-sm text-text-secondary">
          We've detected {suggestions.length} pattern{suggestions.length !== 1 ? 's' : ''} that could be automated with rules
        </p>
      </div>

      {suggestions.length === 0 ? (
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-6 text-center">
          <svg className="mx-auto h-12 w-12 text-primary-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-sm font-medium text-primary-900 mb-1">No Patterns Detected</h3>
          <p className="text-sm text-primary-700">
            We didn't find any recurring patterns in this import that would benefit from automation rules.
            You can create rules manually later from the Rules page.
          </p>
        </div>
      ) : (
        <>
          {/* Summary Card */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z"/>
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-purple-900">Smart Analysis Complete</h3>
                <p className="mt-1 text-sm text-purple-700">
                  We analyzed {analysisResult?.total_transactions_analyzed || 0} transactions and found {suggestions.length} potential rule
                  {suggestions.length !== 1 ? 's' : ''}.
                  Select which rules you'd like to create now. High-confidence patterns are pre-selected.
                </p>
              </div>
            </div>
          </div>

          {/* Suggestions List */}
          <div className="space-y-3">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedSuggestions.has(index)
                    ? "border-primary-500 bg-primary-50"
                    : "border-border hover:border-border"
                }`}
                onClick={() => toggleSuggestion(index)}
              >
                <div className="flex items-start">
                  <input
                    type="checkbox"
                    checked={selectedSuggestions.has(index)}
                    onChange={() => toggleSuggestion(index)}
                    className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-border rounded"
                  />
                  <div className="ml-3 flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-text-primary">
                        {suggestion.suggested_name}
                      </h4>
                      {getConfidenceBadge(suggestion.confidence)}
                    </div>

                    <div className="mt-2 space-y-1 text-sm text-text-secondary">
                      <p>
                        <span className="font-medium">Pattern:</span> Contains "{suggestion.payee_pattern}"
                        {suggestion.detected_merchant && (
                          <span className="ml-2 text-success-700">
                            (Detected: {suggestion.detected_merchant})
                          </span>
                        )}
                      </p>
                      {suggestion.extracted_payee_name && (
                        <p>
                          <span className="font-medium">Extracted Payee:</span> {suggestion.extracted_payee_name}
                          {suggestion.extraction_confidence && (
                            <span className="ml-2 text-xs text-text-tertiary">
                              ({Math.round(suggestion.extraction_confidence * 100)}% extraction quality)
                            </span>
                          )}
                        </p>
                      )}
                      <p>
                        <span className="font-medium">Matches:</span> {suggestion.matching_row_indices.length} transaction
                        {suggestion.matching_row_indices.length !== 1 ? 's' : ''} in this import
                      </p>
                    </div>

                    {/* Sample Descriptions */}
                    {suggestion.sample_descriptions.length > 0 && (
                      <div className="mt-3 bg-surface-secondary rounded p-2">
                        <p className="text-xs font-medium text-text-secondary mb-1">Example transactions:</p>
                        <ul className="space-y-1">
                          {suggestion.sample_descriptions.slice(0, 3).map((desc, idx) => (
                            <li key={idx} className="text-xs text-text-secondary truncate">
                              • {desc}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Info Box */}
          <div className="bg-surface-secondary border border-border rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-text-disabled" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-text-secondary">
                  <strong>Note:</strong> Rules created here will help automatically categorize similar transactions in the future.
                  You can edit or assign categories to these rules later from the Rules page.
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <button
          onClick={onBack}
          disabled={creatingRules}
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-text-secondary hover:bg-surface-secondary disabled:opacity-50"
        >
          Back
        </button>
        <div className="flex gap-3">
          {suggestions.length > 0 && (
            <button
              onClick={handleSkip}
              disabled={creatingRules}
              className="px-4 py-2 border border-border rounded-md text-sm font-medium text-text-secondary hover:bg-surface-secondary disabled:opacity-50"
            >
              Skip for Now
            </button>
          )}
          <button
            onClick={handleContinue}
            disabled={creatingRules}
            className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {creatingRules
              ? selectedSuggestions.size > 0
                ? "Creating Rules & Checking Duplicates..."
                : "Checking for Duplicates..."
              : selectedSuggestions.size > 0
              ? `Create ${selectedSuggestions.size} Rule${selectedSuggestions.size !== 1 ? 's' : ''} & Continue`
              : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}
