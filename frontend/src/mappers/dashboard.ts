/**
 * Dashboard / Today screen view model.
 * All product logic for the Today screen lives here — components only render.
 */

export interface DayState {
  label: string;
  className: string;
}

export interface NextStep {
  action: string;
  why: string;
  outcome: string;
}

export interface SphereVM {
  name: string;
  score: number;
  delta: number;
  deltaStr: string;
  reason: string;
  color: string;
  deltaColor: string;
}

export interface ScorePoint {
  total: number;
  label: string;
}

export interface TodayVM {
  date: string;
  total: number;
  color: string;
  ringOffset: number;
  ringCircumference: number;
  dayState: DayState;
  scoreDelta: number | null;
  interpretation: string;
  nextStep: NextStep | null;
  topSpheres: SphereVM[];
  blockers: string[];
  supports: string[];
  pessimisticPreview: { text: string; delta: number | null } | null;
  optimisticPreview: { text: string; delta: number | null } | null;
  scoreHistory: ScorePoint[];
}

const R = 85;
const C = 2 * Math.PI * R;

function scoreColor(s: number): string {
  if (s >= 65) return "#22c55e";
  if (s >= 45) return "#a78bfa";
  if (s >= 30) return "#f59e0b";
  return "#ef4444";
}

const STATE_CLASSES: Record<string, string> = {
  "Устойчивость": "state-strong",
  "Восстановление": "state-recovery",
  "Поиск опоры": "state-seeking",
  "Под давлением": "state-pressure",
  "Кризис": "state-crisis",
};

export function buildTodayVM(
  scoreData: any,
  graphData: any,
  scenarioData: any,
  historyData?: any,
): TodayVM {
  const total = scoreData?.total ?? 0;
  const spheres = scoreData?.spheres ?? [];
  const color = scoreColor(total);
  const offset = C - (total / 100) * C;

  // Day state — from backend if available, otherwise derive
  const backendState = scoreData?.daily_state;
  const dayState: DayState = backendState
    ? { label: backendState, className: STATE_CLASSES[backendState] || "state-seeking" }
    : deriveDayState(total);

  // Score delta — from backend
  const scoreDelta = scoreData?.score_delta ?? null;

  // Interpretation — from backend reason if available
  const interpretation = scoreData?.daily_state_reason || deriveInterpretation(total);

  // Next step — from backend if available
  const backendStep = scoreData?.next_step;
  const nextStep: NextStep | null =
    backendStep && backendStep.action
      ? { action: backendStep.action, why: backendStep.why, outcome: backendStep.outcome }
      : null;

  // Top 3 weakest spheres
  const sorted = [...spheres].sort((a: any, b: any) => a.score - b.score);
  const topSpheres: SphereVM[] = sorted.slice(0, 3).map((s: any) => ({
    name: s.sphere,
    score: Math.round(s.score),
    delta: s.delta,
    deltaStr: s.delta > 0 ? `+${s.delta}` : s.delta < 0 ? `${s.delta}` : "—",
    reason: s.reason || "",
    color: scoreColor(s.score),
    deltaColor: s.delta > 0 ? "#22c55e" : s.delta < 0 ? "#ef4444" : "#666",
  }));

  // Blockers and supports from graph
  const nodes = (graphData?.nodes ?? []).filter(
    (n: any) => n.label !== "CheckIn" && n.label !== "Person",
  );
  const blockers = nodes.filter((n: any) => n.label === "Blocker").map((n: any) => n.name).slice(0, 2);
  const supports = [
    ...nodes.filter((n: any) => n.label === "Goal"),
    ...nodes.filter((n: any) => n.label === "Value"),
  ].map((n: any) => n.name).slice(0, 2);

  // Scenario previews
  const scenarios = scenarioData?.scenarios ?? [];
  const pessimistic = scenarios.find((s: any) => s.type === "pessimistic");
  const optimistic = scenarios.find((s: any) => s.type === "optimistic");

  const pessimisticPreview = pessimistic
    ? { text: pessimistic.narrative || pessimistic.title, delta: pessimistic.total_delta ?? null }
    : null;
  const optimisticPreview = optimistic
    ? { text: optimistic.narrative || optimistic.title, delta: optimistic.total_delta ?? null }
    : null;

  // Score history
  const rawHistory = historyData?.history ?? [];
  const scoreHistory: ScorePoint[] = rawHistory.map((h: any, i: number) => ({
    total: Math.round(h.total ?? 0),
    label: i === rawHistory.length - 1 ? "сейчас" : `${rawHistory.length - 1 - i}`,
  }));

  const today = new Date().toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return {
    date: today,
    total: Math.round(total),
    color,
    ringOffset: offset,
    ringCircumference: C,
    dayState,
    scoreDelta: scoreDelta !== 0 ? scoreDelta : null,
    interpretation,
    nextStep,
    topSpheres,
    blockers,
    supports,
    pessimisticPreview,
    optimisticPreview,
    scoreHistory,
  };
}

// Fallbacks — only used if backend doesn't provide these fields yet
function deriveDayState(total: number): DayState {
  if (total >= 75) return { label: "Устойчивость", className: "state-strong" };
  if (total >= 60) return { label: "Восстановление", className: "state-recovery" };
  if (total >= 45) return { label: "Поиск опоры", className: "state-seeking" };
  if (total >= 30) return { label: "Под давлением", className: "state-pressure" };
  return { label: "Кризис", className: "state-crisis" };
}

function deriveInterpretation(total: number): string {
  if (total >= 75) return "Система видит устойчивые опоры. Держи курс.";
  if (total >= 60) return "Часть опор уже собирается. Одно верное действие в день — достаточно.";
  if (total >= 45) return "Не хаос, но и не точка силы. Выбери одно направление.";
  if (total >= 30) return "Давление в нескольких сферах. Но есть направление, где можно начать.";
  return "Сейчас тяжело. Найдём один маленький шаг.";
}
