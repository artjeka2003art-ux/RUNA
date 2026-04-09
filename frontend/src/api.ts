const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export async function startOnboarding(userId: string) {
  const res = await fetch(`${BASE}/onboarding/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  return res.json();
}

export async function sendOnboardingMessage(
  userId: string,
  sessionId: string,
  message: string,
  forceComplete: boolean = false,
) {
  const res = await fetch(`${BASE}/onboarding/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId,
      message,
      force_complete: forceComplete,
    }),
  });
  return res.json();
}

export async function sendCheckinMessage(userId: string, message: string) {
  const res = await fetch(`${BASE}/checkin/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, message }),
  });
  return res.json();
}

export async function getLifeScore(userId: string) {
  const res = await fetch(`${BASE}/dashboard/${userId}/score`);
  return res.json();
}

export async function getGraph(userId: string) {
  const res = await fetch(`${BASE}/dashboard/${userId}/graph`);
  return res.json();
}

export async function getScoreHistory(userId: string) {
  const res = await fetch(`${BASE}/dashboard/${userId}/score-history`);
  return res.json();
}

export async function getScenarios(userId: string) {
  const res = await fetch(`${BASE}/dashboard/${userId}/scenarios`);
  return res.json();
}

export async function getDailyCompass(userId: string) {
  const res = await fetch(`${BASE}/dashboard/${userId}/compass`);
  return res.json();
}

export async function submitOneMoveFeedback(
  userId: string,
  status: "done" | "not_done",
  oneMove: string,
  sphereName: string,
) {
  const res = await fetch(`${BASE}/dashboard/${userId}/one-move-feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, status, one_move: oneMove, sphere_name: sphereName }),
  });
  return res.json();
}

// ── Prediction Query (legacy) ──

export async function sendPredictionQuery(userId: string, question: string, sphereId?: string) {
  const res = await fetch(`${BASE}/prediction/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, question, sphere_id: sphereId || null }),
  });
  return res.json();
}

// ── Decision Workspace ──

export type RoutingMode = "existing_sphere" | "multiple_candidates" | "suggest_new_sphere";

export interface MissingContextItem {
  what: string;
  why_important: string;
  sphere_hint: string;
  routing_mode?: RoutingMode;
  candidate_spheres?: string[];
  suggested_sphere_name?: string;
  routing_reason?: string;
}

export interface QueryAssumption {
  assumption_text: string;
  domain: string;
  status: "confirmed" | "query_implied" | "missing_critical";
  affects_confidence: boolean;
}

export interface ContextCompleteness {
  score: "low" | "medium" | "high";
  known_factors: string[];
  missing: MissingContextItem[];
  assumptions?: QueryAssumption[];
}

export interface LeverageFactor {
  factor: string;
  direction: string;
  weight: "high" | "medium" | "low";
}

export interface ConfidenceCalibration {
  level: "low" | "medium" | "high";
  reason: string;
  limiters: string[];
  suggestions: string[];
}

export interface ScenarioReport {
  variant_label: string;
  most_likely_outcome: string;
  alternative_outcome: string;
  main_risks: string[];
  leverage_factors: LeverageFactor[];
  primary_bottleneck: string;
  dominant_downside: string;
  non_obvious_insight: string;
  condition_that_changes_prediction: string;
  decision_signal: string;
  confidence: "low" | "medium" | "high";
  confidence_reason: string;
  affected_spheres: string[];
  depends_on: string;
  next_step: string;
  _calibration?: ConfidenceCalibration;
  _claim_support?: ClaimSupportSummary;
}

export interface ScenarioComparison {
  summary: string;
  key_tradeoffs: string[];
  safest_variant: string;
  highest_upside_variant: string;
  most_sensitive_factor: string;
  hidden_trap: string;
  ranking_variable: string;
}

export interface ClaimSupport {
  field: string;
  variant: string;
  claim: string;
  decisive: boolean;
  support: "none" | "weak" | "moderate" | "strong";
  support_types: string[];
  evidence_count: number;
}

export interface ClaimSupportSummary {
  total_claims?: number;
  supported?: number;
  unsupported_decisive?: number;
  weak_decisive?: number;
  doc_supported?: number;
  support_ratio?: number;
}

export interface CorrectionResult {
  targeted_claims: string[];
  corrected: string[];
  still_unsupported: string[];
}

export interface PredictionQuality {
  score: "low" | "medium" | "high";
  flags: string[];
  retry_used: boolean;
  genericness_ok?: boolean;
  grounding_ok?: boolean;
  grounding_score?: number;
  grounding_components?: Record<string, number>;
  evidence_used?: string[];
  evidence_missed?: string[];
  claim_support?: ClaimSupportSummary;
  claims?: ClaimSupport[];
  correction?: CorrectionResult | null;
}

export interface DocumentEvidenceItem {
  document_name: string;
  sphere_name?: string;
  evidence_snippet: string;
  evidence_type: string;
  relevance: "high" | "medium" | "low";
  why_it_matters: string;
}

export interface DocumentEvidenceReport {
  items: DocumentEvidenceItem[];
  documents_used: string[];
  documents_not_useful: string[];
  has_relevant_evidence: boolean;
  summary: string;
}

export interface DocumentCandidate {
  document_id: string;
  document_name: string;
  sphere_name: string;
  candidate_score: number;
  candidate_reasons: string[];
  document_type_hint: string;
  selected_for_evidence: boolean;
}

export interface WorkspaceResult {
  question: string;
  question_type: string;
  question_mode?: string;
  restated_question: string;
  variants: string[];
  context_completeness: ContextCompleteness;
  reports: ScenarioReport[];
  comparison: ScenarioComparison | null;
  external_insights: string;
  sources: { title: string; url: string; domain: string }[];
  context_spheres_used?: string[];
  documents_used?: string[];
  document_evidence?: DocumentEvidenceReport;
  document_candidates?: DocumentCandidate[];
  _quality?: PredictionQuality;
  signal_quality?: string;
  signal_coverage?: string;
  typed_missing_fields?: TypedMissingField[];
  existing_investment_profile?: Record<string, unknown>;
  investment_policy?: InvestmentPolicyData;
}

export interface InvestmentPolicyData {
  action_posture: string;
  action_label: string;
  exposure_posture: string;
  exposure_label: string;
  hard_guards: string[];
  soft_limiters: string[];
  why: string;
  what_must_improve: string[];
  confidence: string;
}

export interface TypedMissingField {
  field_key: string;
  label: string;
  why: string;
  capture_type: "select" | "number" | "boolean";
  mode: string;
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  placeholder?: string;
}

export async function sendWorkspaceQuery(
  userId: string,
  question: string,
  variants: string[],
  sphereId?: string,
) {
  const res = await fetch(`${BASE}/prediction/workspace`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      question,
      variants: variants.filter((v) => v.trim()),
      sphere_id: sphereId || null,
    }),
  });
  return res.json();
}

// ── Spheres (Phase A) ──

export async function getSpheres(userId: string) {
  const res = await fetch(`${BASE}/spheres/${userId}`);
  return res.json();
}

export async function getSphereDetail(userId: string, sphereId: string) {
  const res = await fetch(`${BASE}/spheres/${userId}/${sphereId}`);
  return res.json();
}

export async function createSphere(userId: string, name: string) {
  const res = await fetch(`${BASE}/spheres`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, name }),
  });
  return res.json();
}

export async function getEnrichmentPrompts(
  sphereName: string,
  missingWhat: string,
  missingWhy: string,
  question: string,
  allMissing: string[],
): Promise<string[] | null> {
  try {
    const res = await fetch(`${BASE}/spheres/enrichment-prompts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sphere_name: sphereName,
        missing_what: missingWhat,
        missing_why: missingWhy,
        question,
        all_missing: allMissing,
      }),
    });
    const data = await res.json();
    if (data.success && data.data?.prompts) return data.data.prompts;
    return null;
  } catch {
    return null;
  }
}

export async function renameSphere(userId: string, sphereId: string, name: string) {
  const res = await fetch(`${BASE}/spheres/${sphereId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, name }),
  });
  return res.json();
}

export async function deleteSphere(userId: string, sphereId: string) {
  const res = await fetch(`${BASE}/spheres/${sphereId}?user_id=${userId}`, {
    method: "DELETE",
  });
  return res.json();
}

export interface EnrichmentContextPayload {
  missing_what: string;
  missing_why: string;
  question: string;
}

export async function sendSphereMessage(
  userId: string,
  sphereId: string,
  message: string,
  enrichmentContext?: EnrichmentContextPayload | null,
) {
  const body: Record<string, unknown> = { user_id: userId, message };
  if (enrichmentContext) {
    body.enrichment_context = enrichmentContext;
  }
  const res = await fetch(`${BASE}/spheres/${sphereId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

// ── Sphere Documents ──

export interface SphereDocument {
  id: string;
  filename: string;
  status: "uploaded" | "processed" | "failed" | "limited";
  text_length: number;
  uploaded_at: string;
}

export async function getSphereDocuments(userId: string, sphereId: string) {
  const res = await fetch(`${BASE}/spheres/${sphereId}/documents?user_id=${userId}`);
  return res.json();
}

export async function uploadSphereDocument(userId: string, sphereId: string, file: File) {
  const form = new FormData();
  form.append("user_id", userId);
  form.append("file", file);
  const res = await fetch(`${BASE}/spheres/${sphereId}/documents`, {
    method: "POST",
    body: form,
  });
  return res.json();
}

export async function deleteSphereDocument(userId: string, sphereId: string, docId: string) {
  const res = await fetch(`${BASE}/spheres/${sphereId}/documents/${docId}?user_id=${userId}`, {
    method: "DELETE",
  });
  return res.json();
}

// ── Structured Sphere Data ──

export async function getSphereStructuredData(userId: string, sphereId: string) {
  const res = await fetch(`${BASE}/spheres/${sphereId}/structured-data?user_id=${userId}`);
  return res.json();
}

export async function saveSphereStructuredData(userId: string, sphereId: string, data: Record<string, string>) {
  const res = await fetch(`${BASE}/spheres/${sphereId}/structured-data`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, data }),
  });
  return res.json();
}

// ── Investment Profile ──

export interface InvestmentProfile {
  investment_horizon?: "short" | "medium" | "long" | "";
  risk_tolerance?: "low" | "medium" | "high" | "";
  experience_level?: "novice" | "some" | "experienced" | "";
  max_acceptable_drawdown?: string;
  runway_months?: number | null;
  has_debt?: boolean | null;
  has_dependents?: boolean | null;
  monthly_investable_amount?: string;
}

export async function getInvestmentProfile(userId: string) {
  const res = await fetch(`${BASE}/dashboard/${userId}/investment-profile`);
  return res.json();
}

export async function saveInvestmentProfile(userId: string, profile: InvestmentProfile) {
  const res = await fetch(`${BASE}/dashboard/${userId}/investment-profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, profile }),
  });
  return res.json();
}
