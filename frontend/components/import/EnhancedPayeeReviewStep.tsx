"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle, Info, ChevronDown, ChevronUp } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
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

    onComplete("payee_review", decisions);
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
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Failed to load payee analysis. Please try again.</AlertDescription>
      </Alert>
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

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle>Intelligent Payee Matching Results</CardTitle>
          <CardDescription>
            We&apos;ve analyzed {analysis.summary.total_transactions} transactions and matched them
            to your existing payees using patterns and fuzzy matching.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-3xl font-bold text-green-600">
                {analysis.summary.high_confidence_matches}
              </div>
              <div className="text-sm text-gray-600">High Confidence Matches</div>
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
        </CardContent>
      </Card>

      {/* HIGH CONFIDENCE SECTION */}
      {highConfidenceAssignments.length > 0 && (
        <Card className="border-green-200 bg-green-50/30">
          <CardHeader className="cursor-pointer" onClick={() => setHighConfidenceExpanded(!highConfidenceExpanded)}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <CardTitle className="text-green-700">
                  High Confidence Matches ({highConfidenceAssignments.length})
                </CardTitle>
              </div>
              {highConfidenceExpanded ? (
                <ChevronUp className="h-5 w-5 text-green-600" />
              ) : (
                <ChevronDown className="h-5 w-5 text-green-600" />
              )}
            </div>
            <CardDescription className="text-green-600">
              These transactions were matched with {">"}85% confidence. Auto-selected but you can change them.
            </CardDescription>
          </CardHeader>
          {highConfidenceExpanded && (
            <CardContent className="space-y-4">
              {highConfidenceAssignments.map((assignment) => (
                <PayeeAssignmentRow
                  key={assignment.transactionIndex}
                  assignment={assignment}
                  onPayeeSelect={handlePayeeSelect}
                  onNewPayeeNameChange={handleNewPayeeNameChange}
                />
              ))}
            </CardContent>
          )}
        </Card>
      )}

      {/* LOW CONFIDENCE SECTION */}
      {lowConfidenceAssignments.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50/30">
          <CardHeader className="cursor-pointer" onClick={() => setLowConfidenceExpanded(!lowConfidenceExpanded)}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                <CardTitle className="text-yellow-700">
                  Review Recommended ({lowConfidenceAssignments.length})
                </CardTitle>
              </div>
              {lowConfidenceExpanded ? (
                <ChevronUp className="h-5 w-5 text-yellow-600" />
              ) : (
                <ChevronDown className="h-5 w-5 text-yellow-600" />
              )}
            </div>
            <CardDescription className="text-yellow-700">
              These transactions were matched with 70-84% confidence. Please review the suggested matches.
            </CardDescription>
          </CardHeader>
          {lowConfidenceExpanded && (
            <CardContent className="space-y-4">
              {lowConfidenceAssignments.map((assignment) => (
                <PayeeAssignmentRow
                  key={assignment.transactionIndex}
                  assignment={assignment}
                  onPayeeSelect={handlePayeeSelect}
                  onNewPayeeNameChange={handleNewPayeeNameChange}
                />
              ))}
            </CardContent>
          )}
        </Card>
      )}

      {/* NEW PAYEES SECTION */}
      {newPayeeAssignments.length > 0 && (
        <Card className="border-blue-200 bg-blue-50/30">
          <CardHeader className="cursor-pointer" onClick={() => setNewPayeesExpanded(!newPayeesExpanded)}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Info className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-blue-700">
                  New Payees ({newPayeeAssignments.length})
                </CardTitle>
              </div>
              {newPayeesExpanded ? (
                <ChevronUp className="h-5 w-5 text-blue-600" />
              ) : (
                <ChevronDown className="h-5 w-5 text-blue-600" />
              )}
            </div>
            <CardDescription className="text-blue-600">
              These transactions don&apos;t match any existing payees. Edit the suggested names or create new.
            </CardDescription>
          </CardHeader>
          {newPayeesExpanded && (
            <CardContent className="space-y-4">
              {newPayeeAssignments.map((assignment) => (
                <PayeeAssignmentRow
                  key={assignment.transactionIndex}
                  assignment={assignment}
                  onPayeeSelect={handlePayeeSelect}
                  onNewPayeeNameChange={handleNewPayeeNameChange}
                />
              ))}
            </CardContent>
          )}
        </Card>
      )}

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-6">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button onClick={handleContinue}>
          Continue to Import
        </Button>
      </div>
    </div>
  );
}

// Row component for individual payee assignment
function PayeeAssignmentRow({
  assignment,
  onPayeeSelect,
  onNewPayeeNameChange,
}: {
  assignment: PayeeAssignment;
  onPayeeSelect: (transactionIndex: number, payeeId: number | null) => void;
  onNewPayeeNameChange: (transactionIndex: number, name: string) => void;
}) {
  const isNewPayee = assignment.matchType === "NO_MATCH";
  const hasMatch = assignment.matchedPayeeId !== undefined;

  return (
    <div className="grid grid-cols-2 gap-4 p-4 bg-white rounded-lg border">
      <div className="space-y-1">
        <Label className="text-xs text-gray-500">Transaction</Label>
        <p className="text-sm font-medium truncate" title={assignment.originalDescription}>
          {assignment.originalDescription}
        </p>
        {hasMatch && (
          <p className="text-xs text-gray-500">
            {assignment.matchReason} • {Math.round((assignment.matchConfidence || 0) * 100)}% confident
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label className="text-xs text-gray-500">
          {isNewPayee ? "New Payee Name (editable)" : "Payee"}
        </Label>

        {isNewPayee ? (
          <Input
            value={assignment.selectedNewPayeeName || ""}
            onChange={(e) => onNewPayeeNameChange(assignment.transactionIndex, e.target.value)}
            placeholder="Enter payee name"
            className="w-full"
          />
        ) : (
          <Select
            value={assignment.selectedPayeeId?.toString() || ""}
            onValueChange={(value) =>
              onPayeeSelect(assignment.transactionIndex, value ? Number(value) : null)
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select payee" />
            </SelectTrigger>
            <SelectContent>
              {/* Matched payee (if any) */}
              {assignment.matchedPayeeId && (
                <SelectItem value={assignment.matchedPayeeId.toString()}>
                  {assignment.matchedPayeeName} (Suggested)
                </SelectItem>
              )}

              {/* Alternative matches */}
              {assignment.alternativeMatches.map((alt) => (
                <SelectItem key={alt.payee_id} value={alt.payee_id.toString()}>
                  {alt.payee_name} ({Math.round(alt.confidence * 100)}%)
                </SelectItem>
              ))}

              {/* Option to create new */}
              <SelectItem value="new">+ Create New Payee</SelectItem>
            </SelectContent>
          </Select>
        )}
      </div>
    </div>
  );
}
