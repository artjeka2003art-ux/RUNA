import { useState, useEffect, useCallback } from "react";
import {
  sendWorkspaceQuery,
  getSpheres,
  getInvestmentProfile,
  saveInvestmentProfile,
  type WorkspaceResult,
  type ScenarioReport,
  type ContextCompleteness,
  type ScenarioComparison,
  type LeverageFactor,
  type MissingContextItem,
  type PredictionQuality,
  type InvestmentProfile,
  type TypedMissingField,
  type InvestmentPolicyData,
  type DocumentEvidenceReport,
} from "./api";
import type { DecisionBridge } from "./App";

// ── Typed missing context field configs ──
// Mode-specific field definitions for structured capture.
// Investment is the first mode pack; pattern is reusable.

interface TypedFieldConfig {
  key: string;
  label: string;
  why: string;
  type: "select" | "number" | "boolean";
  options?: { value: string; label: string }[];
  placeholder?: string;
}

const INVESTMENT_FIELDS: TypedFieldConfig[] = [
  {
    key: "investment_horizon",
    label: "Горизонт инвестирования",
    why: "Влияет на то, считать ли просадку критичной",
    type: "select",
    options: [
      { value: "short", label: "Краткосрочный (< 1 года)" },
      { value: "medium", label: "Среднесрочный (1–3 года)" },
      { value: "long", label: "Долгосрочный (3+ лет)" },
    ],
  },
  {
    key: "risk_tolerance",
    label: "Толерантность к риску",
    why: "Влияет на допустимый тип входа и размер позиции",
    type: "select",
    options: [
      { value: "low", label: "Низкая — не готов терять" },
      { value: "medium", label: "Умеренная" },
      { value: "high", label: "Высокая — готов к просадкам" },
    ],
  },
  {
    key: "experience_level",
    label: "Опыт инвестирования",
    why: "Новичкам нужны более осторожные рекомендации",
    type: "select",
    options: [
      { value: "novice", label: "Новичок" },
      { value: "some", label: "Базовый опыт" },
      { value: "experienced", label: "Опытный инвестор" },
    ],
  },
  {
    key: "runway_months",
    label: "Финансовая подушка (месяцев)",
    why: "Без подушки инвестировать в волатильные активы опасно",
    type: "number",
    placeholder: "Например: 6",
  },
  {
    key: "max_acceptable_drawdown",
    label: "Допустимая просадка",
    why: "Определяет acceptable volatility",
    type: "select",
    options: [
      { value: "10%", label: "До 10%" },
      { value: "30%", label: "До 30%" },
      { value: "50%+", label: "50% и больше" },
    ],
  },
  {
    key: "has_debt",
    label: "Есть долги / кредиты",
    why: "Инвестирование при долгах увеличивает суммарный риск",
    type: "boolean",
  },
  {
    key: "has_dependents",
    label: "Есть зависимые (семья, дети)",
    why: "Потеря капитала затрагивает не только вас",
    type: "boolean",
  },
];

// MISSING_TO_KEY removed — now using structured contract from backend

// ── Workspace state persistence ──

const WS_STORAGE_KEY = "runa_workspace_state";

interface WorkspaceState {
  question: string;
  variants: string[];
  result: WorkspaceResult | null;
  timestamp: number;
}

const WS_TTL = 24 * 60 * 60 * 1000; // 24 hours

function saveWorkspaceState(state: WorkspaceState) {
  try {
    localStorage.setItem(WS_STORAGE_KEY, JSON.stringify(state));
  } catch { /* quota exceeded */ }
}

function loadWorkspaceState(): WorkspaceState | null {
  try {
    const raw = localStorage.getItem(WS_STORAGE_KEY);
    if (!raw) return null;
    const state = JSON.parse(raw) as WorkspaceState;
    if (Date.now() - state.timestamp > WS_TTL) {
      localStorage.removeItem(WS_STORAGE_KEY);
      return null;
    }
    return state;
  } catch {
    return null;
  }
}

// ── Sphere matching ──

interface SphereRef {
  id: string;
  name: string;
}

/** Common Russian sphere synonyms/aliases → canonical tokens */
const SPHERE_SYNONYMS: Record<string, string[]> = {
  "финанс":    ["деньги", "бюджет", "доход", "зарплата", "накопления", "подушка", "финансов"],
  "карьер":    ["работа", "профессия", "должность", "рост", "повышение", "компания", "офис"],
  "здоровь":   ["спорт", "режим", "сон", "тело", "медицин", "врач", "болезн"],
  "отношени":  ["партнёр", "партнер", "семья", "любовь", "брак", "близкие", "друзья", "социальн"],
  "образован": ["учёба", "учеба", "магистратура", "курс", "обучени", "навык"],
  "проект":    ["стартап", "бизнес", "запуск", "свой", "предприниматель"],
  "эмоцион":   ["психолог", "терапи", "ментальн", "выгоран", "стресс", "тревог"],
  "семь":      ["дети", "ребёнок", "ребенок", "родители", "мама", "папа"],
};

function normalize(s: string): string {
  return s.toLowerCase().trim().replace(/[ёЁ]/g, "е");
}

function tokenize(s: string): string[] {
  return normalize(s).split(/[\s,.\-—/]+/).filter((t) => t.length > 1);
}

function matchSphereScore(hint: string, sphereName: string): number {
  const hNorm = normalize(hint);
  const sNorm = normalize(sphereName);

  // Exact match
  if (hNorm === sNorm) return 1.0;

  // Contains
  if (sNorm.includes(hNorm) || hNorm.includes(sNorm)) return 0.85;

  // Token overlap
  const hTokens = tokenize(hint);
  const sTokens = tokenize(sphereName);
  if (hTokens.length > 0 && sTokens.length > 0) {
    let overlap = 0;
    for (const ht of hTokens) {
      for (const st of sTokens) {
        if (st.includes(ht) || ht.includes(st)) {
          overlap++;
          break;
        }
      }
    }
    const tokenScore = overlap / Math.max(hTokens.length, sTokens.length);
    if (tokenScore >= 0.5) return 0.6 + tokenScore * 0.2;
  }

  // Synonym match: check if hint tokens match any synonym group that also matches sphere tokens
  for (const [root, aliases] of Object.entries(SPHERE_SYNONYMS)) {
    const allTerms = [root, ...aliases];
    const hintMatchesSynonym = allTerms.some((t) => hNorm.includes(t));
    const sphereMatchesSynonym = allTerms.some((t) => sNorm.includes(t));
    if (hintMatchesSynonym && sphereMatchesSynonym) return 0.7;
  }

  return 0;
}

function findBestSphere(hint: string, spheres: SphereRef[]): string | null {
  if (!hint || spheres.length === 0) return null;

  let bestId: string | null = null;
  let bestScore = 0;

  for (const s of spheres) {
    const score = matchSphereScore(hint, s.name);
    if (score > bestScore) {
      bestScore = score;
      bestId = s.id;
    }
  }

  // Only return if confident enough
  return bestScore >= 0.5 ? bestId : null;
}

// ── Prediction diff ──

interface DiffItem {
  type: "positive" | "negative" | "neutral";
  text: string;
}

const CONF_ORDER: Record<string, number> = { low: 0, medium: 1, high: 2 };

/** Match a report from prev results by label — exact, then token overlap, then positional fallback */
function matchReport(reports: ScenarioReport[], label: string): ScenarioReport | undefined {
  const norm = normalize(label);
  // Exact normalized match
  const exact = reports.find((r) => normalize(r.variant_label) === norm);
  if (exact) return exact;
  // Token overlap: if >50% tokens match
  const labelTokens = tokenize(label);
  if (labelTokens.length > 0) {
    let bestScore = 0;
    let bestReport: ScenarioReport | undefined;
    for (const r of reports) {
      const rTokens = tokenize(r.variant_label);
      let overlap = 0;
      for (const lt of labelTokens) {
        if (rTokens.some((rt) => rt.includes(lt) || lt.includes(rt))) overlap++;
      }
      const score = overlap / Math.max(labelTokens.length, rTokens.length);
      if (score > bestScore && score >= 0.4) {
        bestScore = score;
        bestReport = r;
      }
    }
    if (bestReport) return bestReport;
  }
  return undefined;
}

function computeDiff(prev: WorkspaceResult, next: WorkspaceResult): DiffItem[] {
  const items: DiffItem[] = [];

  // Context completeness change
  const prevConf = prev.context_completeness?.score || "low";
  const nextConf = next.context_completeness?.score || "low";
  if (prevConf !== nextConf) {
    const improved = (CONF_ORDER[nextConf] ?? 0) > (CONF_ORDER[prevConf] ?? 0);
    items.push({
      type: improved ? "positive" : "negative",
      text: `Полнота контекста: ${CONFIDENCE_LABELS[prevConf]} → ${CONFIDENCE_LABELS[nextConf]}`,
    });
  }

  // New known factors
  const prevKnown = new Set((prev.context_completeness?.known_factors || []).map(normalize));
  const newKnown = (next.context_completeness?.known_factors || []).filter(
    (f) => !prevKnown.has(normalize(f)),
  );
  if (newKnown.length > 0) {
    items.push({
      type: "positive",
      text: `Стало известно больше: ${newKnown.join(", ")}`,
    });
  }

  // Missing context count
  const prevMissing = prev.context_completeness?.missing?.length ?? 0;
  const nextMissing = next.context_completeness?.missing?.length ?? 0;
  if (nextMissing < prevMissing) {
    items.push({
      type: "positive",
      text: `Пробелов стало меньше: ${prevMissing} → ${nextMissing}`,
    });
  } else if (nextMissing > prevMissing) {
    items.push({
      type: "neutral",
      text: `Обнаружены новые пробелы контекста: ${prevMissing} → ${nextMissing}`,
    });
  }

  // Per-scenario confidence changes (with fuzzy label matching)
  for (const nextReport of next.reports) {
    const prevReport = matchReport(prev.reports, nextReport.variant_label);
    if (!prevReport) continue;

    const pConf = prevReport.confidence || "low";
    const nConf = nextReport.confidence || "low";
    if (pConf !== nConf) {
      const improved = (CONF_ORDER[nConf] ?? 0) > (CONF_ORDER[pConf] ?? 0);
      items.push({
        type: improved ? "positive" : "negative",
        text: `«${nextReport.variant_label}»: confidence ${CONFIDENCE_LABELS[pConf]} → ${CONFIDENCE_LABELS[nConf]}`,
      });
    }

    // New risks
    const prevRisks = new Set(prevReport.main_risks?.map(normalize) || []);
    const newRisks = (nextReport.main_risks || []).filter((r) => !prevRisks.has(normalize(r)));
    if (newRisks.length > 0) {
      items.push({
        type: "neutral",
        text: `«${nextReport.variant_label}»: новые риски — ${newRisks.join("; ")}`,
      });
    }

    // Removed risks
    const nextRisks = new Set(nextReport.main_risks?.map(normalize) || []);
    const goneRisks = (prevReport.main_risks || []).filter((r) => !nextRisks.has(normalize(r)));
    if (goneRisks.length > 0) {
      items.push({
        type: "positive",
        text: `«${nextReport.variant_label}»: снятые риски — ${goneRisks.join("; ")}`,
      });
    }

    // Leverage factor changes
    const prevLF = new Set(prevReport.leverage_factors?.map((f) => normalize(f.factor)) || []);
    const newLF = (nextReport.leverage_factors || []).filter((f) => !prevLF.has(normalize(f.factor)));
    if (newLF.length > 0) {
      items.push({
        type: "neutral",
        text: `«${nextReport.variant_label}»: новые ключевые факторы — ${newLF.map((f) => f.factor).join(", ")}`,
      });
    }
  }

  // Assumptions reduced
  const prevAssumptions = (prev.context_completeness?.assumptions || []).filter(a => a.status !== "confirmed");
  const nextAssumptions = (next.context_completeness?.assumptions || []).filter(a => a.status !== "confirmed");
  if (prevAssumptions.length > 0 && nextAssumptions.length < prevAssumptions.length) {
    const resolved = prevAssumptions.length - nextAssumptions.length;
    items.push({
      type: "positive",
      text: `Снято допущений: ${resolved} (базовый контекст подтверждён)`,
    });
  }

  // Resolved missing items (by what)
  const prevMissingWhats = new Set((prev.context_completeness?.missing || []).map(m => normalize(m.what)));
  const resolvedItems = (prev.context_completeness?.missing || [])
    .filter(m => !new Set((next.context_completeness?.missing || []).map(m2 => normalize(m2.what))).has(normalize(m.what)));
  if (resolvedItems.length > 0 && resolvedItems.length <= 5) {
    items.push({
      type: "positive",
      text: `Закрыты пробелы: ${resolvedItems.map(m => m.what).join(", ")}`,
    });
  }

  // Remaining gaps (honest feedback)
  const remainingMissing = next.context_completeness?.missing || [];
  if (remainingMissing.length > 0 && prevMissingWhats.size > 0) {
    items.push({
      type: "neutral",
      text: `Ещё не хватает (${remainingMissing.length}): ${remainingMissing.slice(0, 3).map(m => m.what).join(", ")}${remainingMissing.length > 3 ? "..." : ""}`,
    });
  }

  // Comparison changes
  if (prev.comparison && next.comparison) {
    if (prev.comparison.safest_variant !== next.comparison.safest_variant &&
        next.comparison.safest_variant) {
      items.push({
        type: "neutral",
        text: `Самый безопасный вариант изменился: «${next.comparison.safest_variant}»`,
      });
    }
    if (prev.comparison.most_sensitive_factor !== next.comparison.most_sensitive_factor &&
        next.comparison.most_sensitive_factor) {
      items.push({
        type: "neutral",
        text: `Самый чувствительный фактор теперь: ${next.comparison.most_sensitive_factor}`,
      });
    }
  }

  if (items.length === 0) {
    items.push({ type: "neutral", text: "Существенных изменений не обнаружено." });
  }

  // Generate causal explanation based on what changed
  const cause = inferProbableCause(prev, next, items);
  if (cause) {
    items.unshift({ type: "positive", text: cause });
  }

  return items;
}

/** Infer a human-readable probable cause for prediction improvement */
function inferProbableCause(prev: WorkspaceResult, next: WorkspaceResult, items: DiffItem[]): string | null {
  const prevKnown = prev.context_completeness?.known_factors || [];
  const nextKnown = next.context_completeness?.known_factors || [];
  const newKnown = nextKnown.filter((f) => !prevKnown.map(normalize).includes(normalize(f)));

  const prevMissing = prev.context_completeness?.missing?.length ?? 0;
  const nextMissing = next.context_completeness?.missing?.length ?? 0;
  const missingReduced = prevMissing > nextMissing;

  const prevConf = CONF_ORDER[prev.context_completeness?.score || "low"] ?? 0;
  const nextConf = CONF_ORDER[next.context_completeness?.score || "low"] ?? 0;
  const confImproved = nextConf > prevConf;

  // Build cause string
  if (newKnown.length > 0 && confImproved) {
    return `Вероятная причина улучшения: добавлены данные — ${newKnown.slice(0, 3).join(", ")}`;
  }
  if (newKnown.length > 0) {
    return `Прогноз обновлён с учётом новых факторов: ${newKnown.slice(0, 3).join(", ")}`;
  }
  if (missingReduced && confImproved) {
    return "Прогноз стал увереннее — заполнены ранее недостающие данные";
  }
  if (confImproved) {
    return "Прогноз стал увереннее после обновления контекста";
  }
  if (missingReduced) {
    return "Пробелов стало меньше — контекст стал полнее";
  }

  // Check if risks changed significantly
  const hasPositive = items.some((i) => i.type === "positive" && i.text.includes("риски"));
  if (hasPositive) {
    return "Оценка рисков изменилась после обновления контекста";
  }

  return null;
}

// ── Constants ──

interface WorkspaceSphereContext {
  missingWhat: string;
  missingWhy: string;
  question?: string;
  allMissing?: { what: string; why: string }[];
}

const TYPE_LABELS: Record<string, string> = {
  decision: "Решение",
  trajectory: "Траектория",
  change_impact: "Эффект изменения",
  relationship: "Отношения",
  pattern_risk: "Паттерн / риск",
};

const CONFIDENCE_LABELS: Record<string, string> = {
  low: "Низкая",
  medium: "Средняя",
  high: "Высокая",
};

const CONFIDENCE_COLORS: Record<string, string> = {
  low: "#ef4444",
  medium: "#f59e0b",
  high: "#22c55e",
};

const WEIGHT_LABELS: Record<string, string> = {
  high: "Сильное",
  medium: "Среднее",
  low: "Слабое",
};

// ── Main component ──

interface PredictionViewProps {
  userId: string;
  onNavigateToSphere?: (sphereId: string, ctx: WorkspaceSphereContext) => void;
  onCreateSphereAndNavigate?: (sphereName: string, ctx: WorkspaceSphereContext) => void;
  returnedFromSphere?: boolean;
  onClearReturned?: () => void;
  decisionBridge?: DecisionBridge | null;
  onClearBridge?: () => void;
}

export default function PredictionView({
  userId,
  onNavigateToSphere,
  onCreateSphereAndNavigate,
  returnedFromSphere,
  onClearReturned,
  decisionBridge,
  onClearBridge,
}: PredictionViewProps) {
  const [question, setQuestion] = useState("");
  const [variants, setVariants] = useState<string[]>([""]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkspaceResult | null>(null);
  const [diff, setDiff] = useState<DiffItem[] | null>(null);
  const [spheres, setSpheres] = useState<SphereRef[]>([]);
  const [contextUpdated, setContextUpdated] = useState(false);
  const [bridgeActive, setBridgeActive] = useState(false);

  // Load spheres
  useEffect(() => {
    getSpheres(userId).then((res) => {
      if (res.success && res.data?.spheres) {
        setSpheres(res.data.spheres.map((s: { id: string; name: string }) => ({
          id: s.id,
          name: s.name,
        })));
      }
    }).catch(() => {});
  }, [userId]);

  // Apply decision bridge from onboarding (takes priority over saved state)
  useEffect(() => {
    if (decisionBridge && decisionBridge.draft_question) {
      setQuestion(decisionBridge.draft_question);
      setVariants(
        decisionBridge.draft_variants.length > 0
          ? decisionBridge.draft_variants
          : [""],
      );
      setResult(null);
      setBridgeActive(true);
      onClearBridge?.();
      return;
    }
    // Restore from localStorage only if no bridge
    const saved = loadWorkspaceState();
    if (saved) {
      setQuestion(saved.question);
      setVariants(saved.variants.length > 0 ? saved.variants : [""]);
      setResult(saved.result);
    }
  }, []);

  // Show re-run banner only when truly returned from sphere
  useEffect(() => {
    if (returnedFromSphere && result) {
      setContextUpdated(true);
      onClearReturned?.();
    }
  }, [returnedFromSphere]);

  // Persist
  const persistState = useCallback(() => {
    if (question.trim()) {
      saveWorkspaceState({ question, variants, result, timestamp: Date.now() });
    }
  }, [question, variants, result]);

  useEffect(() => { persistState(); }, [persistState]);

  function addVariant() { setVariants((v) => [...v, ""]); }
  function removeVariant(i: number) { setVariants((v) => v.filter((_, idx) => idx !== i)); }
  function updateVariant(i: number, val: string) { setVariants((v) => v.map((x, idx) => idx === i ? val : x)); }

  async function handleAnalyze() {
    const q = question.trim();
    if (!q || loading) return;

    // Capture previous result for diff before clearing
    const snapshotPrev = result;

    setLoading(true);
    setResult(null);
    setDiff(null);
    setContextUpdated(false);
    try {
      const res = await sendWorkspaceQuery(userId, q, variants);
      if (res.success && res.data) {
        const newResult = res.data as WorkspaceResult;
        setResult(newResult);
        if (snapshotPrev) {
          setDiff(computeDiff(snapshotPrev, newResult));
        }
      }
    } catch { /* ignore */ }
    setLoading(false);
  }

  function findSphereId(hint: string): string | null {
    return findBestSphere(hint, spheres);
  }

  /** Collect all missing items that route to the same sphere */
  function buildSphereContext(item: MissingContextItem, targetHint: string): WorkspaceSphereContext {
    const allMissing = (result?.context_completeness?.missing || [])
      .filter((m) => {
        if (m.routing_mode === "existing_sphere" && m.sphere_hint) {
          return findSphereId(m.sphere_hint) === findSphereId(targetHint);
        }
        if (m.routing_mode === "multiple_candidates" && m.candidate_spheres) {
          return m.candidate_spheres.some((c) => findSphereId(c) === findSphereId(targetHint));
        }
        return false;
      })
      .map((m) => ({ what: m.what, why: m.why_important }));

    return {
      missingWhat: item.what,
      missingWhy: item.why_important,
      question: question || result?.question || "",
      allMissing: allMissing.length > 1 ? allMissing : undefined,
    };
  }

  function handleMissingContextClick(item: MissingContextItem) {
    if (!item.sphere_hint) return;
    const sphereId = findSphereId(item.sphere_hint);
    if (sphereId && onNavigateToSphere) {
      persistState();
      onNavigateToSphere(sphereId, buildSphereContext(item, item.sphere_hint));
    }
  }

  function handleMissingCandidateClick(sphereName: string, item: MissingContextItem) {
    if (!onNavigateToSphere) return;
    const sphereId = findSphereId(sphereName);
    if (!sphereId) return;
    persistState();
    onNavigateToSphere(sphereId, buildSphereContext(item, sphereName));
  }

  function handleCreateSphereClick(item: MissingContextItem) {
    const name = item.suggested_sphere_name || item.sphere_hint;
    if (!name || !onCreateSphereAndNavigate) return;
    persistState();
    onCreateSphereAndNavigate(name, {
      missingWhat: item.what,
      missingWhy: item.why_important,
      question: question || result?.question || "",
    });
  }

  return (
    <div className="ws-view">
      <div className="ws-header">
        <h2>Decision Workspace</h2>
        <p className="ws-subtitle">Смоделируй варианты решения и сравни последствия</p>
      </div>

      {/* Decision bridge banner */}
      {bridgeActive && !result && (
        <div className="ws-bridge-banner">
          <div className="ws-bridge-text">
            <strong>Первая развилка из онбординга</strong>
            <span>{decisionBridge?.bridge_reason || "Мы нашли главную развилку в вашей жизни — начнём с неё."}</span>
          </div>
          <p className="ws-bridge-hint">Это стартовый draft — можете отредактировать вопрос и варианты перед запуском.</p>
          <button className="ws-bridge-dismiss" onClick={() => setBridgeActive(false)}>Понятно</button>
        </div>
      )}

      {/* Context updated banner */}
      {contextUpdated && result && (
        <div className="ws-updated-banner">
          <span>Контекст мог измениться. Пересчитай прогноз для актуального результата.</span>
          <button className="ws-rerun-btn" onClick={handleAnalyze} disabled={loading}>
            Пересчитать прогноз
          </button>
        </div>
      )}

      {/* Question */}
      <div className="ws-section">
        <label className="ws-label">Твой вопрос</label>
        <input
          className="ws-input"
          type="text"
          placeholder="Что будет, если я...?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleAnalyze(); }}
          disabled={loading}
        />
      </div>

      {/* Variants */}
      <div className="ws-section">
        <label className="ws-label">Варианты сценариев</label>
        <p className="ws-hint">Добавь варианты для сравнения. Если оставить пустым — система предложит свои.</p>
        <div className="ws-variants">
          {variants.map((v, i) => (
            <div key={i} className="ws-variant-row">
              <span className="ws-variant-num">{i + 1}</span>
              <input
                className="ws-variant-input"
                type="text"
                placeholder={`Вариант ${i + 1}, напр. "уволиться в июне"`}
                value={v}
                onChange={(e) => updateVariant(i, e.target.value)}
                disabled={loading}
              />
              {variants.length > 1 && (
                <button className="ws-variant-remove" onClick={() => removeVariant(i)} disabled={loading} title="Удалить">
                  &times;
                </button>
              )}
            </div>
          ))}
          <button className="ws-variant-add" onClick={addVariant} disabled={loading}>
            + Добавить вариант
          </button>
        </div>
      </div>

      <button className="ws-run-btn" onClick={handleAnalyze} disabled={loading || !question.trim()}>
        {loading ? "Анализирую сценарии..." : result ? "Пересчитать прогноз" : "Запустить анализ"}
      </button>

      {loading && (
        <div className="ws-loading">
          <div className="spinner" />
          <p>Строю сценарии и сравниваю варианты...</p>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="ws-results">
          {/* Diff block — shown after re-run with confidence headline */}
          {diff && diff.length > 0 && <DiffBlock items={diff} />}
          {diff && diff.length > 0 && (() => {
            const confItem = diff.find((d) => d.text.includes("Полнота контекста:"));
            if (!confItem) return null;
            const improved = confItem.type === "positive";
            return (
              <div className={`ws-confidence-headline ${improved ? "ws-conf-up" : "ws-conf-same"}`}>
                {improved ? "Прогноз стал увереннее" : "Контекст обновлён"}
                <span className="ws-confidence-headline-detail">{confItem.text}</span>
              </div>
            );
          })()}

          {/* Type + restated question */}
          <div className="ws-result-header">
            <span className="ws-type-badge">
              {TYPE_LABELS[result.question_type] || result.question_type}
            </span>
            {result._quality && (
              <QualityBadge quality={result._quality} />
            )}
            {result.restated_question && (
              <div className="ws-restated">"{result.restated_question}"</div>
            )}
          </div>

          <ContextCompletenessBlock
            data={result.context_completeness}
            onMissingClick={handleMissingContextClick}
            onCandidateClick={handleMissingCandidateClick}
            onCreateSphere={handleCreateSphereClick}
            findSphereId={findSphereId}
          />

          {result.investment_policy && (
            <InvestmentPolicyBlock policy={result.investment_policy} />
          )}

          {result.question_mode === "investment" && (result.typed_missing_fields?.length || 0) > 0 && (
            <TypedContextCapture
              userId={userId}
              backendFields={result.typed_missing_fields!}
              existingProfile={result.existing_investment_profile || {}}
              onSaved={handleAnalyze}
            />
          )}

          {result.reports.length > 0 && (
            <div className="ws-block">
              <h3 className="ws-block-title">Сценарии</h3>
              <div className="ws-reports">
                {result.reports.map((r, i) => (
                  <ReportCard key={i} report={r} />
                ))}
              </div>
            </div>
          )}

          {result.comparison && result.reports.length > 1 && (
            <ComparisonBlock
              data={result.comparison}
              reports={result.reports}
              missingCount={result.context_completeness?.missing?.length || 0}
              rankingVariable={result.comparison.ranking_variable}
            />
          )}

          {result.external_insights && (
            <div className="ws-block">
              <h3 className="ws-block-title">Что говорят источники</h3>
              <p className="ws-text">{result.external_insights}</p>
            </div>
          )}

          {/* Document evidence */}
          {result.document_evidence?.has_relevant_evidence && (
            <div className="ws-block ws-doc-evidence">
              <h3 className="ws-block-title">Факты из ваших документов</h3>
              {result.document_evidence.summary && (
                <p className="ws-text ws-doc-evidence-summary">{result.document_evidence.summary}</p>
              )}
              <div className="ws-doc-evidence-items">
                {result.document_evidence.items.map((item, i) => (
                  <div key={i} className={`ws-doc-evidence-item ws-doc-evidence-${item.relevance}${item.is_hard_fact ? " ws-doc-evidence-hard" : ""}`}>
                    <div className="ws-doc-evidence-header">
                      <span className="ws-doc-evidence-file">{item.document_name}</span>
                      {item.is_hard_fact && (
                        <span className="ws-doc-evidence-confirmed">&#10003; Подтверждено</span>
                      )}
                      <span className={`ws-doc-evidence-relevance ws-relevance-${item.relevance}`}>
                        {item.relevance === "high" ? "Ключевой" : item.relevance === "medium" ? "Важный" : "Справочный"}
                      </span>
                    </div>
                    {item.is_hard_fact && item.exact_value ? (
                      <p className="ws-doc-evidence-exact">{item.exact_value}</p>
                    ) : (
                      <p className="ws-doc-evidence-snippet">{item.evidence_snippet}</p>
                    )}
                    <p className="ws-doc-evidence-why">{item.why_it_matters}</p>
                  </div>
                ))}
              </div>
              {result.document_evidence.documents_not_useful?.length > 0 && (
                <p className="ws-doc-not-useful">
                  Не содержат релевантных фактов: {result.document_evidence.documents_not_useful.join(", ")}
                </p>
              )}
            </div>
          )}

          {/* No useful documents notice */}
          {result.document_evidence && !result.document_evidence.has_relevant_evidence && result.documents_used && result.documents_used.length > 0 && (
            <div className="ws-block ws-doc-evidence ws-doc-evidence-empty">
              <h3 className="ws-block-title">Документы</h3>
              <p className="ws-text">Загруженные документы не содержат фактов, напрямую релевантных этому вопросу.</p>
            </div>
          )}

          {/* Context transparency + document routing */}
          {(result.context_spheres_used?.length || result.document_candidates?.length) ? (
            <div className="ws-block ws-context-used">
              <h3 className="ws-block-title">Использованный контекст</h3>
              <div className="ws-context-tags">
                {result.context_spheres_used?.map((s, i) => (
                  <span key={`s-${i}`} className="ws-tag ws-tag-sphere">{s}</span>
                ))}
              </div>
              {result.document_candidates && result.document_candidates.length > 0 && (
                <div className="ws-doc-routing">
                  <div className="ws-doc-routing-label">Документы</div>
                  {result.document_candidates.filter(c => c.selected_for_evidence).map((c, i) => (
                    <div key={`sel-${i}`} className="ws-doc-routing-item ws-doc-routing-selected">
                      <span className="ws-doc-routing-icon">&#10003;</span>
                      <span className="ws-doc-routing-name">{c.document_name}</span>
                      {c.document_type_hint && c.document_type_hint !== "unknown" && (
                        <span className="ws-doc-routing-type">{c.document_type_hint}</span>
                      )}
                      <span className="ws-doc-routing-sphere">{c.sphere_name}</span>
                      <span className="ws-doc-routing-reason">{c.candidate_reasons[0]}</span>
                    </div>
                  ))}
                  {result.document_candidates.filter(c => !c.selected_for_evidence).length > 0 && (
                    <div className="ws-doc-routing-rejected-summary">
                      {result.document_candidates.filter(c => !c.selected_for_evidence).map(c => c.document_name).join(", ")} — не подошли для этого вопроса
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : null}

          {result.sources?.length > 0 && (
            <div className="ws-block">
              <h3 className="ws-block-title">Источники</h3>
              <div className="ws-sources">
                {result.sources.map((s, i) => (
                  <a key={i} className="ws-source" href={s.url} target="_blank" rel="noopener noreferrer">
                    <span className="ws-source-domain">{s.domain}</span>
                    <span className="ws-source-title">{s.title}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Diff Block ── */

const DIFF_ICONS: Record<string, string> = {
  positive: "+",
  negative: "−",
  neutral: "~",
};

function DiffBlock({ items }: { items: DiffItem[] }) {
  // First item may be the causal explanation — render it prominently
  const hasCause = items.length > 1 && (items[0].text.startsWith("Вероятная причина") || items[0].text.startsWith("Прогноз") || items[0].text.startsWith("Пробелов") || items[0].text.startsWith("Оценка"));
  const causeItem = hasCause ? items[0] : null;
  const restItems = hasCause ? items.slice(1) : items;

  return (
    <div className="ws-block ws-diff-block">
      <h3 className="ws-block-title">Что изменилось после обновления контекста</h3>
      {causeItem && (
        <div className="ws-diff-cause">
          <span className="ws-diff-cause-text">{causeItem.text}</span>
        </div>
      )}
      <div className="ws-diff-list">
        {restItems.map((item, i) => (
          <div key={i} className={`ws-diff-item ws-diff-${item.type}`}>
            <span className="ws-diff-icon">{DIFF_ICONS[item.type]}</span>
            <span className="ws-diff-text">{item.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Context Completeness ── */

function ContextCompletenessBlock({
  data,
  onMissingClick,
  onCandidateClick,
  onCreateSphere,
  findSphereId,
}: {
  data: ContextCompleteness;
  onMissingClick: (item: MissingContextItem) => void;
  onCandidateClick: (sphereName: string, item: MissingContextItem) => void;
  onCreateSphere: (item: MissingContextItem) => void;
  findSphereId: (hint: string) => string | null;
}) {
  if (!data) return null;
  const color = CONFIDENCE_COLORS[data.score] || CONFIDENCE_COLORS.low;

  return (
    <div className="ws-block ws-context-block">
      <h3 className="ws-block-title">
        Полнота контекста
        <span className="ws-confidence-badge" style={{ color, borderColor: color }}>
          {CONFIDENCE_LABELS[data.score] || data.score}
        </span>
      </h3>

      {data.known_factors?.length > 0 && (
        <div className="ws-context-known">
          <span className="ws-mini-label">Известно:</span>
          <div className="ws-tag-list">
            {data.known_factors.map((f, i) => (
              <span key={i} className="ws-tag ws-tag-known">{f}</span>
            ))}
          </div>
        </div>
      )}

      {data.assumptions && data.assumptions.filter(a => a.status !== "confirmed").length > 0 && (
        <div className="ws-context-assumptions">
          <span className="ws-mini-label">⚠ Допущения (не подтверждено):</span>
          <div className="ws-assumption-list">
            {data.assumptions.filter(a => a.status !== "confirmed").map((a, i) => (
              <div key={i} className={`ws-assumption-item ws-assumption-${a.status}`}>
                <span>{a.assumption_text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.missing?.length > 0 && (
        <div className="ws-context-missing">
          <span className="ws-mini-label">Чего не хватает:</span>
          <div className="ws-missing-list">
            {data.missing.map((m, i) => {
              const mode = m.routing_mode || "existing_sphere";
              return (
                <div key={i} className="ws-missing-item">
                  <div className="ws-missing-what">{m.what}</div>
                  <div className="ws-missing-why">{m.why_important}</div>

                  {mode === "existing_sphere" && m.sphere_hint && (() => {
                    const hasLink = findSphereId(m.sphere_hint);
                    return hasLink ? (
                      <button
                        className="ws-missing-sphere ws-missing-sphere-link"
                        onClick={() => onMissingClick(m)}
                      >
                        Перейти в сферу: {m.sphere_hint} →
                      </button>
                    ) : (
                      <span className="ws-missing-sphere">{m.sphere_hint}</span>
                    );
                  })()}

                  {mode === "multiple_candidates" && m.candidate_spheres && m.candidate_spheres.length > 0 && (
                    <div className="ws-missing-candidates">
                      <span className="ws-missing-candidates-label">Подходят несколько сфер:</span>
                      <div className="ws-missing-candidates-list">
                        {m.candidate_spheres.map((name, j) => {
                          const sid = findSphereId(name);
                          return sid ? (
                            <button
                              key={j}
                              className="ws-missing-sphere ws-missing-sphere-link ws-missing-candidate"
                              onClick={() => onCandidateClick(name, m)}
                            >
                              {name} →
                            </button>
                          ) : (
                            <span key={j} className="ws-missing-sphere ws-missing-candidate">{name}</span>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {mode === "suggest_new_sphere" && (
                    <div className="ws-missing-suggest-new">
                      {onCreateSphere ? (
                        <button
                          className="ws-missing-sphere ws-missing-sphere-create"
                          onClick={() => onCreateSphere(m)}
                        >
                          + Создать сферу «{m.suggested_sphere_name || m.sphere_hint}»
                        </button>
                      ) : (
                        <span className="ws-missing-sphere ws-missing-sphere-new">
                          Нужна новая сфера: {m.suggested_sphere_name || m.sphere_hint}
                        </span>
                      )}
                      {m.routing_reason && (
                        <span className="ws-missing-routing-reason">{m.routing_reason}</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Report Card ── */

function ReportCard({ report }: { report: ScenarioReport }) {
  const confColor = CONFIDENCE_COLORS[report.confidence] || CONFIDENCE_COLORS.low;
  return (
    <div className="ws-report-card">
      <div className="ws-report-head">
        <div className="ws-report-label">{report.variant_label}</div>
        <span className="ws-confidence-badge" style={{ color: confColor, borderColor: confColor }}
              title={report.confidence_reason || ""}>
          {CONFIDENCE_LABELS[report.confidence] || report.confidence}
        </span>
      </div>

      {/* Calibrated confidence explanation */}
      {report._calibration && (report._calibration.limiters.length > 0 || report._calibration.suggestions.length > 0) && (
        <div className="ws-confidence-detail">
          {report.confidence_reason && (
            <div className="ws-conf-reason">{report.confidence_reason}</div>
          )}
          {report._calibration.suggestions.length > 0 && (
            <div className="ws-conf-suggestions">
              {report._calibration.suggestions.map((s, i) => (
                <span key={i} className="ws-conf-suggestion">{s}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Decision signal — top-level verdict */}
      {report.decision_signal && (
        <div className="ws-report-signal">
          {report.decision_signal}
        </div>
      )}

      <div className="ws-report-section">
        <span className="ws-mini-label">Наиболее вероятный исход</span>
        <p className="ws-text">{report.most_likely_outcome}</p>
      </div>
      {report.alternative_outcome && (
        <div className="ws-report-section">
          <span className="ws-mini-label">Альтернативный исход</span>
          <p className="ws-text ws-text-muted">{report.alternative_outcome}</p>
        </div>
      )}

      {/* Sharp analysis fields */}
      {report.primary_bottleneck && (
        <div className="ws-report-section ws-report-sharp">
          <span className="ws-mini-label ws-label-bottleneck">Главный bottleneck</span>
          <p className="ws-text">{report.primary_bottleneck}</p>
        </div>
      )}
      {report.dominant_downside && (
        <div className="ws-report-section ws-report-sharp">
          <span className="ws-mini-label ws-label-downside">Скрытая цена</span>
          <p className="ws-text">{report.dominant_downside}</p>
        </div>
      )}
      {report.non_obvious_insight && (
        <div className="ws-report-section ws-report-insight">
          <span className="ws-mini-label ws-label-insight">Неочевидное</span>
          <p className="ws-text">{report.non_obvious_insight}</p>
        </div>
      )}
      {report.condition_that_changes_prediction && (
        <div className="ws-report-section ws-report-sharp">
          <span className="ws-mini-label">При каком условии прогноз меняется</span>
          <p className="ws-text ws-text-muted">{report.condition_that_changes_prediction}</p>
        </div>
      )}

      {report.main_risks?.length > 0 && (
        <div className="ws-report-section">
          <span className="ws-mini-label">Основные риски</span>
          <ul className="ws-risk-list">
            {report.main_risks.map((r, i) => (<li key={i}>{r}</li>))}
          </ul>
        </div>
      )}
      {report.leverage_factors?.length > 0 && (
        <div className="ws-report-section">
          <span className="ws-mini-label">Что сильнее всего меняет исход</span>
          <div className="ws-leverage-list">
            {report.leverage_factors.map((lf, i) => (<LeverageFactorTag key={i} data={lf} />))}
          </div>
        </div>
      )}
      {report.affected_spheres?.length > 0 && (
        <div className="ws-report-section">
          <span className="ws-mini-label">Затронутые сферы</span>
          <div className="ws-tag-list">
            {report.affected_spheres.map((s, i) => (<span key={i} className="ws-tag">{s}</span>))}
          </div>
        </div>
      )}
      {report.next_step && (
        <div className="ws-report-next">
          <span className="ws-mini-label">Следующий шаг</span>
          <p className="ws-next-text">{report.next_step}</p>
        </div>
      )}
    </div>
  );
}

function LeverageFactorTag({ data }: { data: LeverageFactor }) {
  const weightColor = data.weight === "high" ? "#ef4444" : data.weight === "medium" ? "#f59e0b" : "#71717a";
  return (
    <div className="ws-leverage-item">
      <span className="ws-leverage-factor">{data.factor}</span>
      <span className="ws-leverage-dir">{data.direction}</span>
      <span className="ws-leverage-weight" style={{ color: weightColor }}>
        {WEIGHT_LABELS[data.weight] || data.weight}
      </span>
    </div>
  );
}

const QUALITY_LABELS: Record<string, string> = {
  high: "Sharp",
  medium: "OK",
  low: "Weak",
};

const QUALITY_COLORS: Record<string, string> = {
  high: "#22c55e",
  medium: "#f59e0b",
  low: "#ef4444",
};

function QualityBadge({ quality }: { quality: PredictionQuality }) {
  const color = QUALITY_COLORS[quality.score] || QUALITY_COLORS.low;
  const parts: string[] = [];
  if (quality.genericness_ok === false) parts.push("generic");
  if (quality.grounding_ok === false) {
    const gs = quality.grounding_score != null ? ` (${Math.round(quality.grounding_score * 100)}%)` : "";
    parts.push(`grounding${gs}`);
  }
  const cs = quality.claim_support;
  if (cs?.unsupported_decisive && cs.unsupported_decisive > 0) {
    parts.push(`${cs.unsupported_decisive} unsupported key claim(s)`);
  } else if (cs?.support_ratio != null && cs.support_ratio < 0.5) {
    parts.push(`support ${Math.round(cs.support_ratio * 100)}%`);
  }
  // Correction outcome
  const corr = quality.correction;
  if (corr) {
    if (corr.corrected.length > 0 && corr.still_unsupported.length === 0) {
      parts.push(`${corr.corrected.length} claim(s) fixed`);
    } else if (corr.still_unsupported.length > 0) {
      parts.push(`${corr.still_unsupported.length} still weak`);
    }
  }
  const tooltip = parts.length > 0 ? parts.join(" | ") : "All claims supported";
  return (
    <span
      className="ws-quality-badge"
      style={{ color, borderColor: color }}
      title={tooltip}
    >
      {QUALITY_LABELS[quality.score]}{quality.retry_used ? " (corrected)" : ""}
    </span>
  );
}

function ComparisonBlock({ data, reports, missingCount, rankingVariable }: {
  data: ScenarioComparison;
  reports: ScenarioReport[];
  missingCount: number;
  rankingVariable?: string;
}) {
  // Determine current leader from confidence + summary
  const confOrder: Record<string, number> = { low: 0, medium: 1, high: 2 };
  const sorted = [...reports].sort((a, b) =>
    (confOrder[b.confidence] ?? 0) - (confOrder[a.confidence] ?? 0)
  );
  const leader = data.safest_variant || sorted[0]?.variant_label;
  const leaderReport = reports.find(r => r.variant_label === leader);
  const leaderConf = leaderReport?.confidence || "low";

  // Check if leader is truly better or just better-confirmed
  const allSameConf = reports.every(r => r.confidence === reports[0]?.confidence);
  const highestUpside = data.highest_upside_variant;
  const upsideIsDifferent = highestUpside && highestUpside !== leader;

  return (
    <div className="ws-block ws-comparison-block">
      <h3 className="ws-block-title">Сравнение сценариев</h3>

      {/* Current leader banner */}
      {leader && (
        <div className="ws-comp-leader">
          <div className="ws-comp-leader-row">
            <span className="ws-comp-leader-label">При текущих данных сильнее:</span>
            <span className="ws-comp-leader-name">{leader}</span>
            <span className="ws-confidence-badge ws-comp-leader-conf"
                  style={{ color: CONFIDENCE_COLORS[leaderConf], borderColor: CONFIDENCE_COLORS[leaderConf] }}>
              {CONFIDENCE_LABELS[leaderConf]}
            </span>
          </div>
          {missingCount > 0 && (
            <div className="ws-comp-leader-caveat">
              Сравнение ограничено — не хватает {missingCount} {missingCount === 1 ? "элемента" : missingCount < 5 ? "элементов" : "элементов"} контекста
            </div>
          )}
        </div>
      )}

      {/* Summary verdict */}
      {data.summary && <p className="ws-text ws-comp-summary">{data.summary}</p>}

      {/* Scenario confidence comparison */}
      {reports.length > 1 && !allSameConf && (
        <div className="ws-comp-conf-compare">
          <span className="ws-mini-label">Уверенность по сценариям</span>
          <div className="ws-comp-conf-bars">
            {reports.map((r, i) => {
              const conf = r.confidence || "low";
              const color = CONFIDENCE_COLORS[conf] || CONFIDENCE_COLORS.low;
              const width = conf === "high" ? "100%" : conf === "medium" ? "66%" : "33%";
              return (
                <div key={i} className="ws-comp-conf-row">
                  <span className="ws-comp-conf-label">{r.variant_label}</span>
                  <div className="ws-comp-conf-bar-track">
                    <div className="ws-comp-conf-bar-fill" style={{ width, background: color }} />
                  </div>
                  <span className="ws-comp-conf-level" style={{ color }}>
                    {CONFIDENCE_LABELS[conf]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Trade-offs */}
      {data.key_tradeoffs?.length > 0 && (
        <div className="ws-comp-section">
          <span className="ws-mini-label">Trade-offs: что получаешь и чем платишь</span>
          <div className="ws-tradeoff-cards">
            {data.key_tradeoffs.map((t, i) => (
              <div key={i} className="ws-tradeoff-card">{t}</div>
            ))}
          </div>
        </div>
      )}

      {/* Tension: upside vs safety */}
      {upsideIsDifferent && (
        <div className="ws-comp-tension">
          <div className="ws-comp-tension-item ws-comp-tension-safe">
            <span className="ws-mini-label">Безопаснее</span>
            <span className="ws-comp-tension-name">{data.safest_variant}</span>
          </div>
          <div className="ws-comp-tension-vs">vs</div>
          <div className="ws-comp-tension-item ws-comp-tension-upside">
            <span className="ws-mini-label">Больше потенциал</span>
            <span className="ws-comp-tension-name">{highestUpside}</span>
          </div>
        </div>
      )}

      {/* Hidden trap */}
      {data.hidden_trap && (
        <div className="ws-comp-section ws-comp-trap">
          <span className="ws-mini-label ws-label-downside">Ловушка</span>
          <p className="ws-text">{data.hidden_trap}</p>
        </div>
      )}

      {/* Sensitive factor + ranking variable */}
      <div className="ws-comp-grid">
        {data.most_sensitive_factor && (
          <div className="ws-comp-cell">
            <span className="ws-mini-label">Что сильнее всего меняет расклад</span>
            <span className="ws-comp-value ws-comp-factor">{data.most_sensitive_factor}</span>
          </div>
        )}
        {rankingVariable && (
          <div className="ws-comp-cell">
            <span className="ws-mini-label">Что узнать для окончательного выбора</span>
            <span className="ws-comp-value">{rankingVariable}</span>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Investment Policy Block ── */

const POSTURE_COLORS: Record<string, string> = {
  avoid_now: "#ef4444",
  wait_for_clarity: "#f59e0b",
  exploratory_entry: "#3b82f6",
  small_dca: "#22c55e",
  normal_dca: "#10b981",
};

const POSTURE_ICONS: Record<string, string> = {
  avoid_now: "🛑",
  wait_for_clarity: "⏳",
  exploratory_entry: "🔍",
  small_dca: "📈",
  normal_dca: "✅",
};

function InvestmentPolicyBlock({ policy }: { policy: InvestmentPolicyData }) {
  const color = POSTURE_COLORS[policy.action_posture] || "#94a3b8";
  const icon = POSTURE_ICONS[policy.action_posture] || "📋";
  const hasGuards = policy.hard_guards.length > 0;

  return (
    <div className="ws-policy-block" style={{ borderColor: color + "40" }}>
      <div className="ws-policy-header">
        <span className="ws-policy-icon">{icon}</span>
        <div className="ws-policy-action" style={{ color }}>
          {policy.action_label}
        </div>
        <span className="ws-policy-confidence" title="Уверенность в рекомендации">
          {policy.confidence === "high" ? "●●●" : policy.confidence === "medium" ? "●●○" : "●○○"}
        </span>
      </div>

      <div className="ws-policy-exposure">
        <span className="ws-policy-exposure-label">Допустимый размер:</span>
        <span className="ws-policy-exposure-value">{policy.exposure_label}</span>
      </div>

      <div className="ws-policy-why">{policy.why}</div>

      {hasGuards && (
        <div className="ws-policy-guards">
          {policy.hard_guards.map((g, i) => {
            const text = g.includes(": ") ? g.split(": ", 2)[1] : g;
            return (
              <div key={i} className="ws-policy-guard">🛑 {text}</div>
            );
          })}
        </div>
      )}

      {!hasGuards && policy.soft_limiters.length > 0 && (
        <div className="ws-policy-limiters">
          {policy.soft_limiters.slice(0, 3).map((l, i) => (
            <div key={i} className="ws-policy-limiter">⚠ {l}</div>
          ))}
        </div>
      )}

      {policy.what_must_improve.length > 0 && (
        <div className="ws-policy-improve">
          <span className="ws-policy-improve-title">Что должно измениться:</span>
          {policy.what_must_improve.slice(0, 3).map((w, i) => (
            <div key={i} className="ws-policy-improve-item">→ {w}</div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Typed Missing Context Capture (backend-driven) ── */

function TypedContextCapture({
  userId,
  backendFields,
  existingProfile,
  onSaved,
}: {
  userId: string;
  backendFields: TypedMissingField[];
  existingProfile: Record<string, unknown>;
  onSaved: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<Record<string, string | number | boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  // Prefill existing values when opening
  useEffect(() => {
    if (!open) return;
    const prefilled: Record<string, string | number | boolean> = {};
    for (const f of backendFields) {
      const existing = existingProfile[f.field_key];
      if (existing !== undefined && existing !== null && existing !== "") {
        prefilled[f.field_key] = existing as string | number | boolean;
      }
    }
    setValues(prev => ({ ...prefilled, ...prev }));
  }, [open]);

  const handleChange = (key: string, value: string | number | boolean, field: TypedMissingField) => {
    // Basic validation
    const newErrors = { ...errors };
    if (field.capture_type === "number") {
      const num = typeof value === "number" ? value : Number(value);
      if (isNaN(num)) {
        newErrors[key] = "Введите число";
      } else if (field.min !== undefined && num < field.min) {
        newErrors[key] = `Минимум: ${field.min}`;
      } else if (field.max !== undefined && num > field.max) {
        newErrors[key] = `Максимум: ${field.max}`;
      } else {
        delete newErrors[key];
      }
    } else {
      delete newErrors[key];
    }
    setErrors(newErrors);
    setValues(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    if (saving || Object.keys(errors).length > 0) return;
    setSaving(true);
    try {
      const profile: Record<string, unknown> = { ...existingProfile };
      for (const [k, v] of Object.entries(values)) {
        if (v !== "" && v !== undefined) {
          profile[k] = v;
        }
      }
      await saveInvestmentProfile(userId, profile as InvestmentProfile);
      setOpen(false);
      setValues({});
      setErrors({});
      onSaved();
    } catch { /* silent */ }
    setSaving(false);
  };

  const filledCount = Object.entries(values).filter(
    ([k, v]) => v !== "" && v !== undefined && v !== existingProfile[k]
  ).length;
  const hasErrors = Object.keys(errors).length > 0;
  const n = backendFields.length;

  return (
    <div className="ws-typed-capture">
      {!open ? (
        <div className="ws-typed-capture-prompt" onClick={() => setOpen(true)}>
          <div className="ws-typed-capture-icon">⚡</div>
          <div className="ws-typed-capture-text">
            <strong>Повысить точность прогноза</strong>
            <span>
              Уточни {n} параметр{n === 1 ? "" : n < 5 ? "а" : "ов"} — прогноз пересчитается автоматически
            </span>
          </div>
          <div className="ws-typed-capture-arrow">→</div>
        </div>
      ) : (
        <div className="ws-typed-capture-panel">
          <div className="ws-typed-capture-header">
            <strong>Уточни параметры для точного прогноза</strong>
            <button className="ws-typed-capture-close" onClick={() => setOpen(false)}>✕</button>
          </div>
          <div className="ws-typed-capture-fields">
            {backendFields.map(f => (
              <div key={f.field_key} className="ws-typed-field">
                <label className="ws-typed-field-label">{f.label}</label>
                <span className="ws-typed-field-why">{f.why}</span>
                {f.capture_type === "select" && f.options && (
                  <div className="ws-typed-chips">
                    {f.options.map(opt => (
                      <button
                        key={opt.value}
                        className={`ws-typed-chip ${values[f.field_key] === opt.value ? "ws-typed-chip-active" : ""}`}
                        onClick={() => handleChange(f.field_key, opt.value, f)}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}
                {f.capture_type === "number" && (
                  <>
                    <input
                      type="number"
                      className={`ws-typed-input ${errors[f.field_key] ? "ws-typed-input-error" : ""}`}
                      placeholder={f.placeholder}
                      min={f.min}
                      max={f.max}
                      value={values[f.field_key] as number ?? ""}
                      onChange={e => handleChange(
                        f.field_key,
                        e.target.value ? Number(e.target.value) : "",
                        f
                      )}
                    />
                    {errors[f.field_key] && (
                      <span className="ws-typed-error">{errors[f.field_key]}</span>
                    )}
                  </>
                )}
                {f.capture_type === "boolean" && (
                  <div className="ws-typed-chips">
                    <button
                      className={`ws-typed-chip ${values[f.field_key] === true ? "ws-typed-chip-active" : ""}`}
                      onClick={() => handleChange(f.field_key, true, f)}
                    >Да</button>
                    <button
                      className={`ws-typed-chip ${values[f.field_key] === false ? "ws-typed-chip-active" : ""}`}
                      onClick={() => handleChange(f.field_key, false, f)}
                    >Нет</button>
                  </div>
                )}
              </div>
            ))}
          </div>
          <button
            className="ws-typed-save"
            onClick={handleSave}
            disabled={saving || filledCount === 0 || hasErrors}
          >
            {saving ? "Сохраняю..." : `Сохранить и пересчитать${filledCount > 0 ? ` (${filledCount})` : ""}`}
          </button>
        </div>
      )}
    </div>
  );
}
