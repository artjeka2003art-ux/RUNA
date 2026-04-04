import { useState, useEffect } from "react";
import { getLifeScore, getGraph, getScenarios, getScoreHistory, getDailyCompass, submitOneMoveFeedback } from "./api";
import { buildTodayVM, type TodayVM } from "./mappers/dashboard";

const R = 85;

export default function Dashboard({ userId }: { userId: string }) {
  const [vm, setVm] = useState<TodayVM | null>(null);
  const [loading, setLoading] = useState(true);

  // One Move feedback state — MUST be before any conditional return
  const [moveFeedback, setMoveFeedback] = useState<{
    status: "done" | "not_done";
    message: string;
    scoreImpact: number;
  } | null>(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [scoreRes, graphRes, historyRes, compassRes] = await Promise.all([
        getLifeScore(userId),
        getGraph(userId),
        getScoreHistory(userId).catch(() => ({ success: false, data: null })),
        getDailyCompass(userId).catch(() => ({ success: false, data: null })),
      ]);
      let scenarioData = null;
      try {
        const scenRes = await getScenarios(userId);
        if (scenRes.success) scenarioData = scenRes.data;
      } catch {}

      const scoreData = scoreRes.success ? scoreRes.data : null;
      const graphData = graphRes.success ? graphRes.data : null;
      const historyData = historyRes.success ? historyRes.data : null;
      const compassData = compassRes.success ? compassRes.data : null;

      setVm(buildTodayVM(scoreData, graphData, scenarioData, historyData, compassData));
      setLoading(false);
    }
    load();
  }, [userId]);

  if (loading || !vm) {
    return <div className="today"><div className="today-loading"><div className="spinner" /></div></div>;
  }

  const compass = vm.compass;
  const historyPoints = vm.scoreHistory;
  const hasHistory = historyPoints.length >= 2;

  async function handleMoveFeedback(status: "done" | "not_done") {
    if (feedbackLoading || moveFeedback) return;
    setFeedbackLoading(true);
    try {
      const res = await submitOneMoveFeedback(
        userId, status,
        compass?.oneMove || "",
        compass?.focusSphere?.name || "",
      );
      if (res.success && res.data) {
        setMoveFeedback({
          status: res.data.status,
          message: res.data.message,
          scoreImpact: res.data.score_impact || 0,
        });
      }
    } catch {} finally {
      setFeedbackLoading(false);
    }
  }

  return (
    <div className="today">
      <div className="today-date">{vm.date}</div>

      {/* ── YESTERDAY'S ACTION TRACE ── */}
      {compass?.lastActionTrace && (
        <div className={`compass-card compass-card--trace compass-card--trace-${compass.lastActionTrace.status}`}>
          <div className="compass-card-icon">{compass.lastActionTrace.status === "done" ? "↗" : "·"}</div>
          <div className="compass-card-body">
            <p className="compass-card-text">{compass.lastActionTrace.message}</p>
          </div>
        </div>
      )}

      {/* ── COMPASS HERO ── */}
      <div className="compass-hero">
        <div className="compass-hero-left">
          <div className="hero-score-ring hero-score-ring--small">
            <svg className="score-ring-svg" viewBox="0 0 200 200">
              <circle className="score-ring-bg" cx="100" cy="100" r={R} />
              <circle className="score-ring-fill" cx="100" cy="100" r={R} stroke={vm.color} strokeDasharray={vm.ringCircumference} strokeDashoffset={vm.ringOffset} />
            </svg>
            <div className="score-ring-center">
              <span className="score-ring-number" style={{ color: vm.color }}>{vm.total}</span>
              <span className="score-ring-label">Life Score</span>
            </div>
          </div>
          {vm.scoreDelta != null && (
            <span className="compass-delta" style={{ color: vm.scoreDelta > 0 ? "#22c55e" : "#ef4444" }}>
              {vm.scoreDelta > 0 ? "+" : ""}{vm.scoreDelta}
            </span>
          )}
        </div>
        <div className="compass-hero-right">
          <span className={`compass-state ${compass ? "state-from-compass" : vm.dayState.className}`}>
            {compass?.dailyState || vm.dayState.label}
          </span>
          <p className="compass-state-reason">
            {compass?.dailyStateReason || vm.interpretation}
          </p>
        </div>
      </div>

      {/* ── KEY SHIFT ── */}
      {compass?.keyShiftTitle && (
        <div className="compass-card compass-card--shift">
          <div className="compass-card-icon">&#x2194;</div>
          <div className="compass-card-body">
            <h3 className="compass-card-title">{compass.keyShiftTitle}</h3>
            <p className="compass-card-text">{compass.keyShiftReason}</p>
          </div>
        </div>
      )}

      {/* ── FOCUS SPHERE ── */}
      {compass?.focusSphere && (
        <div className="compass-card compass-card--focus" onClick={() => {
          window.dispatchEvent(new CustomEvent("runa-navigate", {
            detail: { tab: "sphere-detail", sphereId: compass.focusSphere!.id },
          }));
        }}>
          <div className="compass-card-body">
            <div className="compass-focus-header">
              <span className="compass-focus-label">Фокус сегодня</span>
              <span className="compass-focus-score" style={{ color: vm.color }}>
                {Math.round(compass.focusSphere.score)}
              </span>
            </div>
            <h3 className="compass-card-title compass-focus-name">{compass.focusSphere.name}</h3>
            <span className="compass-focus-cta">Открыть сферу &rarr;</span>
          </div>
        </div>
      )}

      {/* ── ONE MOVE ── */}
      {compass?.oneMove && (
        <div className="compass-card compass-card--move">
          <div className="compass-card-body">
            <span className="compass-move-label">Один шаг на сегодня</span>
            <h3 className="compass-move-action">{compass.oneMove}</h3>
            {compass.oneMoveReason && (
              <p className="compass-card-text">{compass.oneMoveReason}</p>
            )}
            {moveFeedback ? (
              <div className={`move-feedback move-feedback--${moveFeedback.status}`}>
                <span className="move-feedback-icon">
                  {moveFeedback.status === "done" ? "✓" : "·"}
                </span>
                <span className="move-feedback-message">{moveFeedback.message}</span>
                {moveFeedback.scoreImpact > 0 && (
                  <span className="move-feedback-impact">+{moveFeedback.scoreImpact} к сфере</span>
                )}
              </div>
            ) : (
              <div className="move-actions">
                <button
                  className="move-btn move-btn--done"
                  onClick={() => handleMoveFeedback("done")}
                  disabled={feedbackLoading}
                >
                  {feedbackLoading ? "..." : "Сделал"}
                </button>
                <button
                  className="move-btn move-btn--skip"
                  onClick={() => handleMoveFeedback("not_done")}
                  disabled={feedbackLoading}
                >
                  Не сделал
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── COST OF IGNORING ── */}
      {compass?.costOfIgnoring && (
        <div className="compass-card compass-card--warning">
          <div className="compass-card-icon">&#x26A0;</div>
          <div className="compass-card-body">
            <span className="compass-warning-label">Если не трогать</span>
            <p className="compass-card-text">{compass.costOfIgnoring}</p>
          </div>
        </div>
      )}

      {/* ── FALLBACK: old next step if no compass ── */}
      {!compass && vm.nextStep && (
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

      {/* Score History Trend */}
      {hasHistory && <ScoreSparkline points={historyPoints} color={vm.color} />}

      {/* Key Spheres (secondary) */}
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

/** Minimal SVG sparkline */
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
