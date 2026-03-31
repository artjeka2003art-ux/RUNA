import { useState, useEffect } from "react";
import { getScenarios } from "./api";

interface Scenario {
  type: string;
  title: string;
  narrative: string;
  probability: number;
  total_score_initial: number;
  total_score_final: number;
  total_delta: number;
}

const TYPE_LABELS: Record<string, string> = {
  optimistic: "Оптимистичный",
  realistic: "Реалистичный",
  pessimistic: "Пессимистичный",
};

const TYPE_COLORS: Record<string, string> = {
  optimistic: "#22c55e",
  realistic: "#a78bfa",
  pessimistic: "#ef4444",
};

export default function PredictionView({ userId }: { userId: string }) {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [leverage, setLeverage] = useState("");
  const [warning, setWarning] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await getScenarios(userId);
        if (res.success && res.data.scenarios?.length) {
          setScenarios(res.data.scenarios);
          setLeverage(res.data.key_leverage_point?.narrative || res.data.key_leverage_point?.impact || "");
          setWarning(res.data.warning_signal?.narrative || res.data.warning_signal?.trend || "");
        } else {
          setError(res.data?.message || "Недостаточно данных");
        }
      } catch {
        setError("Ошибка загрузки");
      }
      setLoading(false);
    }
    load();
  }, [userId]);

  if (loading) {
    return (
      <div className="pred-view">
        <h2>Prediction</h2>
        <div className="pred-loading">
          <div className="spinner" />
          <p>Считаю сценарии...</p>
          <span className="pred-method">graph_math / 12w projection</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pred-view">
        <h2>Prediction</h2>
        <p className="empty-state">{error}</p>
      </div>
    );
  }

  return (
    <div className="pred-view">
      <h2>Prediction</h2>
      <span className="pred-method">graph_math / 12w projection</span>

      {scenarios.map((s) => {
        const c = TYPE_COLORS[s.type] || "#888";
        return (
          <div key={s.type} className="sc-card" style={{ borderLeftColor: c }}>
            <div className="sc-head">
              <span className="sc-type" style={{ color: c }}>{TYPE_LABELS[s.type] || s.type}</span>
              <span className="sc-prob" style={{ color: c }}>{s.probability}%</span>
            </div>
            {s.title && <div className="sc-title">{s.title}</div>}
            {s.narrative && <p className="sc-text">{s.narrative}</p>}
            <div className="sc-score">
              <span>{s.total_score_initial}</span>
              <span style={{ color: s.total_delta >= 0 ? "#22c55e" : "#ef4444" }}>
                {s.total_delta >= 0 ? "+" : ""}{s.total_delta}
              </span>
              <span>→ {s.total_score_final}</span>
            </div>
          </div>
        );
      })}

      {leverage && (
        <div className="insight green">
          <div className="insight-tag">Ключевой рычаг</div>
          <p>{leverage}</p>
        </div>
      )}

      {warning && (
        <div className="insight red">
          <div className="insight-tag">Сигнал тревоги</div>
          <p>{warning}</p>
        </div>
      )}
    </div>
  );
}
