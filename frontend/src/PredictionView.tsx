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
  realistic: "Текущий курс",
  optimistic: "Если собраться",
  pessimistic: "Если ничего не менять",
};

const TYPE_COLORS: Record<string, string> = {
  optimistic: "#22c55e",
  realistic: "#a78bfa",
  pessimistic: "#ef4444",
};

const TYPE_ORDER = ["realistic", "optimistic", "pessimistic"];

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
          setError(res.data?.message || "Недостаточно данных для построения маршрутов");
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
      <div className="path-view">
        <div className="path-header">
          <h2>Path</h2>
          <p className="path-subtitle">Строю маршруты...</p>
        </div>
        <div className="path-loading"><div className="spinner" /></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="path-view">
        <div className="path-header">
          <h2>Path</h2>
          <p className="path-subtitle">Три маршрута, по которым сейчас может пойти твоя жизнь</p>
        </div>
        <p className="empty-state">{error}</p>
      </div>
    );
  }

  const sorted = [...scenarios].sort((a, b) => TYPE_ORDER.indexOf(a.type) - TYPE_ORDER.indexOf(b.type));

  return (
    <div className="path-view">
      <div className="path-header">
        <h2>Path</h2>
        <p className="path-subtitle">Три маршрута, по которым сейчас может пойти твоя жизнь</p>
      </div>

      <div className="path-scenarios">
        {sorted.map((s) => {
          const c = TYPE_COLORS[s.type] || "#888";
          const isMain = s.type === "realistic";
          return (
            <div key={s.type} className={`path-card ${isMain ? "path-card-main" : ""}`} style={{ borderLeftColor: c }}>
              <div className="path-card-head">
                <span className="path-card-type" style={{ color: c }}>{TYPE_LABELS[s.type] || s.type}</span>
                <span className="path-card-prob" style={{ color: c }}>{s.probability}%</span>
              </div>
              {s.title && <div className="path-card-title">{s.title}</div>}
              {s.narrative && <p className="path-card-narrative">{s.narrative}</p>}
              <div className="path-card-score">
                <span className="path-score-from">{s.total_score_initial}</span>
                <span className="path-score-arrow">&#x2192;</span>
                <span className="path-score-to">{s.total_score_final}</span>
                <span className="path-score-delta" style={{ color: s.total_delta >= 0 ? "#22c55e" : "#ef4444" }}>
                  ({s.total_delta >= 0 ? "+" : ""}{s.total_delta})
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Leverage & Warning */}
      {(leverage || warning) && (
        <div className="path-insights">
          {leverage && (
            <div className="path-insight-card path-insight-leverage">
              <div className="path-insight-label">Главная точка влияния</div>
              <p>{leverage}</p>
            </div>
          )}
          {warning && (
            <div className="path-insight-card path-insight-warning">
              <div className="path-insight-label">Ранний сигнал риска</div>
              <p>{warning}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
