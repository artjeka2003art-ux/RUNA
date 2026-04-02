/**
 * Path / Scenarios view model.
 * All product logic for the Path screen lives here.
 */

export interface ScenarioVM {
  type: string;
  label: string;
  question: string;
  accent: string;
  isMain: boolean;
  title: string;
  narrative: string;
  probability: number;
  scoreFrom: number;
  scoreTo: number;
  scoreDelta: number;
  risk: string;
  firstStep: string;
  horizonLabel: string;
}

export interface PathVM {
  scenarios: ScenarioVM[];
  leverage: string;
  warning: string;
}

const TYPE_META: Record<string, { label: string; accent: string; question: string }> = {
  realistic: {
    label: "Текущий курс",
    accent: "#a78bfa",
    question: "Куда ты движешься прямо сейчас",
  },
  optimistic: {
    label: "Путь роста",
    accent: "#22c55e",
    question: "Что нужно сделать, чтобы попасть сюда",
  },
  pessimistic: {
    label: "Цена бездействия",
    accent: "#ef4444",
    question: "Что произойдёт, если ничего не менять",
  },
};

const TYPE_ORDER = ["realistic", "optimistic", "pessimistic"];

export function buildPathVM(data: any): PathVM {
  const rawScenarios = data?.scenarios ?? [];
  const leverage = data?.key_leverage_point?.narrative || data?.key_leverage_point?.impact || "";
  const warning = data?.warning_signal?.narrative || data?.warning_signal?.trend || "";

  const scenarios: ScenarioVM[] = rawScenarios
    .sort((a: any, b: any) => TYPE_ORDER.indexOf(a.type) - TYPE_ORDER.indexOf(b.type))
    .map((s: any) => {
      const meta = TYPE_META[s.type] || { label: s.type, accent: "#888", question: "" };
      return {
        type: s.type,
        label: meta.label,
        question: meta.question,
        accent: meta.accent,
        isMain: s.type === "realistic",
        title: s.title || "",
        narrative: s.narrative || "",
        probability: s.probability ?? 33,
        scoreFrom: s.total_score_initial ?? 0,
        scoreTo: s.total_score_final ?? 0,
        scoreDelta: s.total_delta ?? 0,
        // Use backend fields; no frontend fallback guesses
        risk: s.risk || "",
        firstStep: s.first_step || "",
        horizonLabel: s.horizon_label || "",
      };
    });

  return { scenarios, leverage, warning };
}
