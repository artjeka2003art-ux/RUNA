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
  message: string
) {
  const res = await fetch(`${BASE}/onboarding/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, session_id: sessionId, message }),
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

export interface MissingContextItem {
  what: string;
  why_important: string;
  sphere_hint: string;
}

export interface ContextCompleteness {
  score: "low" | "medium" | "high";
  known_factors: string[];
  missing: MissingContextItem[];
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

export interface WorkspaceResult {
  question: string;
  question_type: string;
  restated_question: string;
  variants: string[];
  context_completeness: ContextCompleteness;
  reports: ScenarioReport[];
  comparison: ScenarioComparison | null;
  external_insights: string;
  sources: { title: string; url: string; domain: string }[];
  context_spheres_used?: string[];
  documents_used?: string[];
  _quality?: PredictionQuality;
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

export async function sendSphereMessage(userId: string, sphereId: string, message: string) {
  const res = await fetch(`${BASE}/spheres/${sphereId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, message }),
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
