/**
 * TypeScript types for Intelligent Payee Matching System
 *
 * Corresponds to backend schemas in:
 * backend/app/schemas/intelligent_matching.py
 */

export interface AlternativeMatch {
  payee_id: number;
  payee_name: string;
  confidence: number;
}

export interface TransactionPayeeAnalysis {
  transaction_index: number;
  original_description: string;
  extracted_payee_name: string;
  extraction_confidence: number;

  // Matching results
  match_type: "HIGH_CONFIDENCE" | "LOW_CONFIDENCE" | "NO_MATCH";
  matched_payee_id?: number | null;
  matched_payee_name?: string | null;
  match_confidence: number;
  match_reason: string;

  // Suggested category (from known merchants or matched payee's default)
  suggested_category?: string | null;

  // Alternatives for user selection
  alternative_matches: AlternativeMatch[];
}

export interface IntelligentAnalysisSummary {
  high_confidence_matches: number;
  low_confidence_matches: number;
  new_payees_needed: number;
  total_transactions: number;
  existing_payees_matched: Array<{
    payee_id: number;
    name: string;
    count: number;
  }>;
}

export interface IntelligentPayeeAnalysisResponse {
  analyses: TransactionPayeeAnalysis[];
  summary: IntelligentAnalysisSummary;
}

// Request types for execution

export interface PayeeAssignmentDecision {
  transaction_index: number;
  original_description: string;

  // User can choose EITHER existing payee OR create new one
  payee_id?: number | null;
  new_payee_name?: string | null;
  new_payee_category?: string | null;

  // Whether to create/strengthen pattern from this decision
  create_pattern?: boolean;
}

export interface ImportWithPayeeDecisionsRequest {
  account_id: number;
  skip_rows?: number[];
  payee_assignments: PayeeAssignmentDecision[];
}

// UI state types

export interface PayeeAssignment {
  transactionIndex: number;
  originalDescription: string;
  extractedName: string;

  matchType: "HIGH_CONFIDENCE" | "LOW_CONFIDENCE" | "NO_MATCH";

  // For matches
  matchedPayeeId?: number;
  matchedPayeeName?: string;
  matchConfidence?: number;
  matchReason?: string;

  // Suggested category from analysis
  suggestedCategory?: string | null;

  // For user selection (frontend state)
  selectedPayeeId?: number | null;
  selectedNewPayeeName?: string;

  // Alternatives shown in dropdown
  alternativeMatches: AlternativeMatch[];
}
