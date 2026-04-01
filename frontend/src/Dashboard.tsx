import { useState, useEffect } from "react";
import { getLifeScore, getGraph, getScenarios } from "./api";

interface SphereScore { sphere: string; score: number; delta: number; reason: string; }
interface GraphNode { label: string; name: string; }

function scoreColor(s: number): string {
  if (s >= 65) return "#22c55e";
  if (s >= 45) return "#a78bfa";
  if (s >= 30) return "#f59e0b";
  return "#ef4444";
}

function scoreInterpretation(s: number): string {
  if (s >= 75) return "У тебя сейчас сильная фаза. Система видит устойчивые опоры в нескольких сферах. Важно не терять фокус.";
  if (s >= 60) return "Ты в фазе восстановления. Часть опор уже собирается, но ещё есть внутренний шум. Одно верное действие в день — достаточно.";
  if (s >= 45) return "Сейчас не точка силы, но и не хаос. Главное — не пытаться починить всю жизнь за один день.";
  if (s >= 30) return "Система видит давление в нескольких сферах. Но даже в этом состоянии есть одно направление, где можно начать.";
  return "Сейчас тяжело. Но ты здесь — значит, ты не сдался. Давай найдём один маленький шаг, который ты можешь сделать сегодня.";
}

export default function Dashboard({ userId }: { userId: string }) {
  const [total, setTotal] = useState(0);
  const [spheres, setSpheres] = useState<SphereScore[]>([]);
  const [blockers, setBlockers] = useState<GraphNode[]>([]);
  const [goals, setGoals] = useState<GraphNode[]>([]);
  const [values, setValues] = useState<GraphNode[]>([]);
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [scoreRes, graphRes] = await Promise.all([
        getLifeScore(userId),
        getGraph(userId),
      ]);
      if (scoreRes.success) {
        setTotal(scoreRes.data.total);
        setSpheres(scoreRes.data.spheres || []);
      }
      if (graphRes.success) {
        const n = (graphRes.data.nodes || []).filter((x: GraphNode) => x.label !== "CheckIn" && x.label !== "Person");
        setBlockers(n.filter((x: GraphNode) => x.label === "Blocker"));
        setGoals(n.filter((x: GraphNode) => x.label === "Goal"));
        setValues(n.filter((x: GraphNode) => x.label === "Value"));
      }
      getScenarios(userId).then((r) => {
        if (r.success && r.data.scenarios?.length) setPrediction(r.data);
      }).catch(() => {});
      setLoading(false);
    }
    load();
  }, [userId]);

  if (loading) {
    return <div className="today"><div className="today-loading"><div className="spinner" /></div></div>;
  }

  const color = scoreColor(total);
  const R = 85;
  const C = 2 * Math.PI * R;
  const offset = C - (total / 100) * C;

  const today = new Date().toLocaleDateString("ru-RU", { weekday: "long", day: "numeric", month: "long" });

  // Top 3 spheres by importance (lowest score = most attention needed)
  const topSpheres = [...spheres].sort((a, b) => a.score - b.score).slice(0, 3);

  // Weakest sphere for next step
  const weakest = spheres.length > 0 ? [...spheres].sort((a, b) => a.score - b.score)[0] : null;

  // Scenario previews
  const optimistic = prediction?.scenarios?.find((s: any) => s.type === "optimistic");
  const pessimistic = prediction?.scenarios?.find((s: any) => s.type === "pessimistic");

  return (
    <div className="today">
      <div className="today-date">{today}</div>

      {/* Hero Block */}
      <div className="today-hero">
        <div className="hero-score-ring">
          <svg className="score-ring-svg" viewBox="0 0 200 200">
            <circle className="score-ring-bg" cx="100" cy="100" r={R} />
            <circle className="score-ring-fill" cx="100" cy="100" r={R} stroke={color} strokeDasharray={C} strokeDashoffset={offset} />
          </svg>
          <div className="score-ring-center">
            <span className="score-ring-number" style={{ color }}>{Math.round(total)}</span>
            <span className="score-ring-label">Life Score</span>
          </div>
        </div>
        <div className="hero-text">
          <p className="hero-interpretation">{scoreInterpretation(total)}</p>
        </div>
      </div>

      {/* Key Spheres */}
      {topSpheres.length > 0 && (
        <div className="today-section">
          <h3 className="section-title">Ключевые сферы</h3>
          <div className="spheres-grid">
            {topSpheres.map((s) => {
              const c = scoreColor(s.score);
              const deltaStr = s.delta > 0 ? `+${s.delta}` : s.delta < 0 ? `${s.delta}` : "—";
              return (
                <div key={s.sphere} className="sphere-card">
                  <div className="sphere-card-header">
                    <span className="sphere-card-name">{s.sphere}</span>
                    <span className="sphere-card-score" style={{ color: c }}>{Math.round(s.score)}</span>
                  </div>
                  <div className="sphere-card-bar">
                    <div className="sphere-card-bar-fill" style={{ width: `${s.score}%`, background: c }} />
                  </div>
                  <div className="sphere-card-footer">
                    <span className="sphere-card-delta" style={{ color: s.delta > 0 ? "#22c55e" : s.delta < 0 ? "#ef4444" : "#666" }}>{deltaStr}</span>
                    {s.reason && <span className="sphere-card-reason">{s.reason}</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Two columns: Blockers + Supports */}
      <div className="today-two-col">
        {/* What's pulling you down */}
        <div className="today-card today-card-danger">
          <h3 className="section-title">Что сейчас тянет вниз</h3>
          {blockers.length > 0 ? (
            <ul className="insight-list">
              {blockers.slice(0, 2).map((b) => (
                <li key={b.name} className="insight-list-item danger">{b.name}</li>
              ))}
            </ul>
          ) : (
            <p className="empty-hint">Пока не выявлено. Делай чекины — система найдёт.</p>
          )}
        </div>

        {/* What gives you ground */}
        <div className="today-card today-card-support">
          <h3 className="section-title">Что даёт опору</h3>
          {(goals.length > 0 || values.length > 0) ? (
            <ul className="insight-list">
              {[...goals, ...values].slice(0, 2).map((g) => (
                <li key={g.name} className="insight-list-item support">{g.name}</li>
              ))}
            </ul>
          ) : (
            <p className="empty-hint">Появится после нескольких чекинов.</p>
          )}
        </div>
      </div>

      {/* Next Step */}
      {weakest && (
        <div className="today-card today-card-action">
          <h3 className="section-title">Следующий шаг на сегодня</h3>
          <p className="next-step-text">
            Сфера <strong>{weakest.sphere}</strong> сейчас на {Math.round(weakest.score)} — это самая уязвимая точка.
            {weakest.reason && <> {weakest.reason}</>}
          </p>
          <p className="next-step-why">Одно маленькое действие в этой сфере даст наибольший сдвиг.</p>
        </div>
      )}

      {/* Future Preview */}
      {(optimistic || pessimistic) && (
        <div className="today-section">
          <h3 className="section-title">Что дальше</h3>
          <div className="future-preview">
            {pessimistic && (
              <div className="future-card future-stay">
                <div className="future-label">Если оставить всё как есть</div>
                <p className="future-text">{pessimistic.narrative || pessimistic.title}</p>
                {pessimistic.score_delta != null && (
                  <span className="future-delta" style={{ color: "#ef4444" }}>Life Score: {pessimistic.score_delta > 0 ? "+" : ""}{pessimistic.score_delta}</span>
                )}
              </div>
            )}
            {optimistic && (
              <div className="future-card future-grow">
                <div className="future-label">Если сделать один честный шаг</div>
                <p className="future-text">{optimistic.narrative || optimistic.title}</p>
                {optimistic.score_delta != null && (
                  <span className="future-delta" style={{ color: "#22c55e" }}>Life Score: {optimistic.score_delta > 0 ? "+" : ""}{optimistic.score_delta}</span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="today-cta">
        <p className="cta-hint">Обновить свою картину</p>
        <button className="cta-button" onClick={() => {
          // Navigate to check-in via dispatching a custom event
          window.dispatchEvent(new CustomEvent("runa-navigate", { detail: "checkin" }));
        }}>
          Сделать check-in
        </button>
      </div>
    </div>
  );
}
