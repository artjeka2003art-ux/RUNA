import { useState, useEffect } from "react";
import { getScenarios } from "./api";
import { buildPathVM, type PathVM } from "./mappers/scenarios";

export default function PredictionView({ userId }: { userId: string }) {
  const [vm, setVm] = useState<PathVM | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await getScenarios(userId);
        if (res.success && res.data.scenarios?.length) {
          setVm(buildPathVM(res.data));
        } else {
          setError("Для построения маршрутов нужно больше данных. Сделай несколько чекинов — и система покажет, куда ведёт твой текущий курс.");
        }
      } catch {
        setError("Не удалось загрузить маршруты. Попробуй позже.");
      }
      setLoading(false);
    }
    load();
  }, [userId]);

  if (loading) {
    return (
      <div className="path-view">
        <div className="path-header">
          <h2>Твой путь</h2>
          <p className="path-subtitle">Строю маршруты на основе твоей модели...</p>
        </div>
        <div className="path-loading"><div className="spinner" /></div>
      </div>
    );
  }

  if (error || !vm) {
    return (
      <div className="path-view">
        <div className="path-header"><h2>Твой путь</h2></div>
        <p className="empty-state">{error}</p>
      </div>
    );
  }

  return (
    <div className="path-view">
      <div className="path-header">
        <h2>Твой путь</h2>
        <p className="path-subtitle">Три направления, в которых может двигаться твоя жизнь прямо сейчас</p>
      </div>

      <div className="path-scenarios">
        {vm.scenarios.map((s) => (
          <div key={s.type} className={`path-card ${s.isMain ? "path-card-main" : ""}`} style={{ borderLeftColor: s.accent }}>
            <div className="path-card-head">
              <div>
                <span className="path-card-type" style={{ color: s.accent }}>{s.label}</span>
                <div className="path-card-question">{s.question}</div>
              </div>
              <span className="path-card-prob" style={{ color: s.accent }}>{s.probability}%</span>
            </div>
            {s.title && <div className="path-card-title">{s.title}</div>}
            {s.narrative && <p className="path-card-narrative">{s.narrative}</p>}

            <div className="path-card-meta">
              {s.horizonLabel && (
                <div className="path-card-horizon">
                  <span className="path-meta-label">Горизонт:</span> {s.horizonLabel}
                </div>
              )}
              <div className="path-card-score">
                <span className="path-score-from">{s.scoreFrom}</span>
                <span className="path-score-arrow">&#x2192;</span>
                <span className="path-score-to">{s.scoreTo}</span>
                <span className="path-score-delta" style={{ color: s.scoreDelta >= 0 ? "#22c55e" : "#ef4444" }}>
                  ({s.scoreDelta >= 0 ? "+" : ""}{s.scoreDelta})
                </span>
              </div>
              {s.risk && <div className="path-card-risk"><span className="path-meta-label">Риск:</span> {s.risk}</div>}
              {s.firstStep && <div className="path-card-step"><span className="path-meta-label">Первый шаг:</span> {s.firstStep}</div>}
            </div>
          </div>
        ))}
      </div>

      {(vm.leverage || vm.warning) && (
        <div className="path-insights">
          {vm.leverage && (
            <div className="path-insight-card path-insight-leverage">
              <div className="path-insight-label">Главная точка влияния</div>
              <p>{vm.leverage}</p>
            </div>
          )}
          {vm.warning && (
            <div className="path-insight-card path-insight-warning">
              <div className="path-insight-label">На что обратить внимание</div>
              <p>{vm.warning}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
