import { useState, useEffect } from "react";
import { getLifeScore, getGraph, getScenarios, getScoreHistory } from "./api";
import { buildTodayVM, type TodayVM } from "./mappers/dashboard";

const R = 85;

export default function Dashboard({ userId }: { userId: string }) {
  const [vm, setVm] = useState<TodayVM | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [scoreRes, graphRes, historyRes] = await Promise.all([
        getLifeScore(userId),
        getGraph(userId),
        getScoreHistory(userId).catch(() => ({ success: false, data: null })),
      ]);
      let scenarioData = null;
      try {
        const scenRes = await getScenarios(userId);
        if (scenRes.success) scenarioData = scenRes.data;
      } catch {}

      const scoreData = scoreRes.success ? scoreRes.data : null;
      const graphData = graphRes.success ? graphRes.data : null;
      const historyData = historyRes.success ? historyRes.data : null;

      setVm(buildTodayVM(scoreData, graphData, scenarioData, historyData));
      setLoading(false);
    }
    load();
  }, [userId]);

  if (loading || !vm) {
    return <div className="today"><div className="today-loading"><div className="spinner" /></div></div>;
  }

  // SVG sparkline for score history
  const historyPoints = vm.scoreHistory;
  const hasHistory = historyPoints.length >= 2;

  return (
    <div className="today">
      <div className="today-date">{vm.date}</div>

      {/* Hero */}
      <div className="today-hero">
        <div className="hero-score-ring">
          <svg className="score-ring-svg" viewBox="0 0 200 200">
            <circle className="score-ring-bg" cx="100" cy="100" r={R} />
            <circle className="score-ring-fill" cx="100" cy="100" r={R} stroke={vm.color} strokeDasharray={vm.ringCircumference} strokeDashoffset={vm.ringOffset} />
          </svg>
          <div className="score-ring-center">
            <span className="score-ring-number" style={{ color: vm.color }}>{vm.total}</span>
            <span className="score-ring-label">Life Score</span>
          </div>
        </div>
        <div className="hero-text">
          <div className="hero-state-row">
            <span className={`hero-day-state ${vm.dayState.className}`}>{vm.dayState.label}</span>
            {vm.scoreDelta != null && (
              <span className="hero-score-delta" style={{ color: vm.scoreDelta > 0 ? "#22c55e" : "#ef4444" }}>
                {vm.scoreDelta > 0 ? "+" : ""}{vm.scoreDelta} с прошлого раза
              </span>
            )}
          </div>
          <p className="hero-interpretation">{vm.interpretation}</p>
        </div>
      </div>

      {/* Score History Trend */}
      {hasHistory && <ScoreSparkline points={historyPoints} color={vm.color} />}

      {/* Next Step */}
      {vm.nextStep && (
        <div className="next-step-card">
          <h3 className="next-step-heading">Что сделать сегодня</h3>
          <p className="next-step-action">{vm.nextStep.action}</p>
          <div className="next-step-details">
            <div className="next-step-detail">
              <span className="next-step-detail-label">Почему именно это</span>
              <span className="next-step-detail-text">{vm.nextStep.why}</span>
            </div>
            <div className="next-step-detail">
              <span className="next-step-detail-label">Что изменится</span>
              <span className="next-step-detail-text">{vm.nextStep.outcome}</span>
            </div>
          </div>
        </div>
      )}

      {/* Key Spheres */}
      {vm.topSpheres.length > 0 && (
        <div className="today-section">
          <h3 className="section-title">Сферы, которые требуют внимания</h3>
          <div className="spheres-grid">
            {vm.topSpheres.map((s) => (
              <div key={s.name} className="sphere-card">
                <div className="sphere-card-header">
                  <span className="sphere-card-name">{s.name}</span>
                  <span className="sphere-card-score" style={{ color: s.color }}>{s.score}</span>
                </div>
                <div className="sphere-card-bar">
                  <div className="sphere-card-bar-fill" style={{ width: `${s.score}%`, background: s.color }} />
                </div>
                <div className="sphere-card-footer">
                  <span className="sphere-card-delta" style={{ color: s.deltaColor }}>{s.deltaStr}</span>
                  {s.reason && <span className="sphere-card-reason">{s.reason}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Blockers + Supports */}
      <div className="today-two-col">
        <div className="today-card today-card-danger">
          <h3 className="section-title">Что тормозит</h3>
          {vm.blockers.length > 0 ? (
            <ul className="insight-list">
              {vm.blockers.map((b) => <li key={b} className="insight-list-item danger">{b}</li>)}
            </ul>
          ) : (
            <p className="empty-hint">Система ещё собирает данные. После нескольких чекинов картина станет яснее.</p>
          )}
        </div>
        <div className="today-card today-card-support">
          <h3 className="section-title">На что опереться</h3>
          {vm.supports.length > 0 ? (
            <ul className="insight-list">
              {vm.supports.map((g) => <li key={g} className="insight-list-item support">{g}</li>)}
            </ul>
          ) : (
            <p className="empty-hint">Появится после нескольких разговоров с системой.</p>
          )}
        </div>
      </div>

      {/* Future Preview */}
      {(vm.pessimisticPreview || vm.optimisticPreview) && (
        <div className="today-section">
          <h3 className="section-title">Куда ведёт текущий курс</h3>
          <div className="future-preview">
            {vm.pessimisticPreview && (
              <div className="future-card future-stay">
                <div className="future-label">Цена бездействия</div>
                <p className="future-text">{vm.pessimisticPreview.text}</p>
                {vm.pessimisticPreview.delta != null && (
                  <span className="future-delta" style={{ color: "#ef4444" }}>
                    Life Score: {vm.pessimisticPreview.delta > 0 ? "+" : ""}{vm.pessimisticPreview.delta}
                  </span>
                )}
              </div>
            )}
            {vm.optimisticPreview && (
              <div className="future-card future-grow">
                <div className="future-label">Если начать сегодня</div>
                <p className="future-text">{vm.optimisticPreview.text}</p>
                {vm.optimisticPreview.delta != null && (
                  <span className="future-delta" style={{ color: "#22c55e" }}>
                    Life Score: {vm.optimisticPreview.delta > 0 ? "+" : ""}{vm.optimisticPreview.delta}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="today-cta">
        <button className="cta-button" onClick={() => {
          window.dispatchEvent(new CustomEvent("runa-navigate", { detail: "checkin" }));
        }}>
          Обновить картину — сделать check-in
        </button>
      </div>
    </div>
  );
}

/** Minimal SVG sparkline — no external libraries. */
function ScoreSparkline({ points, color }: { points: { total: number; label: string }[]; color: string }) {
  const W = 320;
  const H = 60;
  const PAD = 8;

  const values = points.map((p) => p.total);
  const min = Math.min(...values) - 5;
  const max = Math.max(...values) + 5;
  const range = max - min || 1;

  const coords = values.map((v, i) => ({
    x: PAD + (i / (values.length - 1)) * (W - PAD * 2),
    y: PAD + (1 - (v - min) / range) * (H - PAD * 2),
  }));

  const polyline = coords.map((c) => `${c.x},${c.y}`).join(" ");
  const last = coords[coords.length - 1];

  return (
    <div className="score-history">
      <h3 className="section-title">Динамика Life Score</h3>
      <svg viewBox={`0 0 ${W} ${H}`} className="sparkline-svg">
        <polyline points={polyline} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.7" />
        {coords.map((c, i) => (
          <circle key={i} cx={c.x} cy={c.y} r={i === coords.length - 1 ? 4 : 2.5} fill={color} opacity={i === coords.length - 1 ? 1 : 0.5} />
        ))}
        <text x={last.x} y={last.y - 8} textAnchor="middle" fill={color} fontSize="10" fontWeight="700">{values[values.length - 1]}</text>
      </svg>
    </div>
  );
}
