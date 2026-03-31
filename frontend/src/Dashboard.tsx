import { useState, useEffect } from "react";
import { getLifeScore, getGraph, getScenarios } from "./api";

interface SphereScore {
  sphere: string;
  score: number;
  delta: number;
  reason: string;
}

interface GraphNode {
  label: string;
  name: string;
}

interface GraphEdge {
  from: string;
  to: string;
  type: string;
  weight: number;
}

interface Scenario {
  type: string;
  title: string;
  narrative: string;
  probability: number;
  total_score_initial: number;
  total_score_final: number;
  total_delta: number;
}

interface DashboardProps {
  userId: string;
  onOpenCheckin: () => void;
}

// ── Node Colors ─────────────────────────────────────────

const NODE_COLORS: Record<string, string> = {
  Sphere: "#818cf8",
  Blocker: "#ef4444",
  Pattern: "#f59e0b",
  Goal: "#22c55e",
  Value: "#a78bfa",
  Event: "#38bdf8",
};

const NODE_LABELS_RU: Record<string, string> = {
  Sphere: "Сфера",
  Blocker: "Блокер",
  Pattern: "Паттерн",
  Goal: "Цель",
  Value: "Ценность",
  Event: "Событие",
};

// ── Visual Graph ────────────────────────────────────────

function VisualGraph({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  const WIDTH = 480;
  const HEIGHT = 400;
  const CX = WIDTH / 2;
  const CY = HEIGHT / 2;

  const visible = nodes.filter((n) => n.label !== "CheckIn" && n.label !== "Person");
  const spheres = visible.filter((n) => n.label === "Sphere");
  const others = visible.filter((n) => n.label !== "Sphere");

  const pos: Record<string, { x: number; y: number }> = {};

  // Spheres in inner ring
  spheres.forEach((n, i) => {
    const a = (i / Math.max(spheres.length, 1)) * Math.PI * 2 - Math.PI / 2;
    pos[n.name] = { x: CX + Math.cos(a) * 90, y: CY + Math.sin(a) * 90 };
  });

  // Others in outer ring, grouped near their connected sphere
  others.forEach((n, i) => {
    // Find which sphere this node connects to
    const connectedEdge = edges.find((e) => e.from === n.name && pos[e.to]);
    if (connectedEdge && pos[connectedEdge.to]) {
      // Place near the connected sphere with some spread
      const spherePos = pos[connectedEdge.to];
      const angleToSphere = Math.atan2(spherePos.y - CY, spherePos.x - CX);
      const spread = ((i % 3) - 1) * 0.5;
      pos[n.name] = {
        x: CX + Math.cos(angleToSphere + spread) * 165,
        y: CY + Math.sin(angleToSphere + spread) * 165,
      };
    } else {
      const a = (i / Math.max(others.length, 1)) * Math.PI * 2 - Math.PI / 2;
      pos[n.name] = { x: CX + Math.cos(a) * 165, y: CY + Math.sin(a) * 165 };
    }
  });

  const visEdges = edges.filter((e) => pos[e.from] && pos[e.to]);

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="graph-svg">
      <defs>
        <radialGradient id="graphGlow">
          <stop offset="0%" stopColor="#6366f1" stopOpacity="0.06" />
          <stop offset="100%" stopColor="transparent" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx={CX} cy={CY} r={190} fill="url(#graphGlow)" />

      {/* Edges */}
      {visEdges.map((e, i) => {
        const f = pos[e.from];
        const t = pos[e.to];
        if (!f || !t) return null;
        // Color edges by type: red for blockers, green for goals
        const fromNode = visible.find((n) => n.name === e.from);
        const edgeColor = fromNode?.label === "Blocker" ? "#ef444440" :
                          fromNode?.label === "Goal" ? "#22c55e40" :
                          "rgba(255,255,255,0.06)";
        return (
          <line
            key={`e-${i}`}
            x1={f.x} y1={f.y} x2={t.x} y2={t.y}
            stroke={edgeColor}
            strokeWidth={Math.max(1, e.weight * 2.5)}
          />
        );
      })}

      {/* Nodes */}
      {visible.map((n) => {
        const p = pos[n.name];
        if (!p) return null;
        const color = NODE_COLORS[n.label] || "#666";
        const isSphere = n.label === "Sphere";
        const r = isSphere ? 32 : 22;
        const truncName = n.name.length > 12 ? n.name.slice(0, 11) + ".." : n.name;

        return (
          <g key={n.name}>
            {/* Glow */}
            {isSphere && (
              <circle cx={p.x} cy={p.y} r={r + 8} fill={color} opacity={0.06} />
            )}
            {/* Node circle */}
            <circle
              cx={p.x} cy={p.y} r={r}
              fill={isSphere ? `${color}15` : "#08080d"}
              stroke={color}
              strokeWidth={isSphere ? 2 : 1}
              strokeOpacity={isSphere ? 0.8 : 0.4}
            />
            {/* Label */}
            <text
              x={p.x} y={p.y + 1}
              textAnchor="middle" dominantBaseline="central"
              fill={color}
              fontSize={isSphere ? 9 : 7.5}
              fontWeight={isSphere ? 600 : 400}
              opacity={isSphere ? 1 : 0.8}
            >
              {truncName}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ── Prediction View ─────────────────────────────────────

function PredictionView({ userId, onClose }: { userId: string; onClose: () => void }) {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [leveragePoint, setLeveragePoint] = useState("");
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
          setLeveragePoint(res.data.key_leverage_point?.narrative || res.data.key_leverage_point?.impact || "");
          setWarning(res.data.warning_signal?.narrative || res.data.warning_signal?.trend || "");
        } else {
          setError(res.data?.message || "Недостаточно данных для prediction");
        }
      } catch {
        setError("Ошибка загрузки");
      }
      setLoading(false);
    }
    load();
  }, [userId]);

  const typeLabels: Record<string, string> = {
    optimistic: "Оптимистичный",
    realistic: "Реалистичный",
    pessimistic: "Пессимистичный",
  };

  const typeColors: Record<string, string> = {
    optimistic: "#22c55e",
    realistic: "#818cf8",
    pessimistic: "#ef4444",
  };

  if (loading) {
    return (
      <div className="prediction-view">
        <div className="prediction-header">
          <h2>Prediction</h2>
          <button onClick={onClose} className="close-btn">&times;</button>
        </div>
        <div className="prediction-loading">
          <div className="spinner" />
          <p>Считаю сценарии...</p>
          <p className="prediction-sublabel">graph math + narrative</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="prediction-view">
        <div className="prediction-header">
          <h2>Prediction</h2>
          <button onClick={onClose} className="close-btn">&times;</button>
        </div>
        <p className="empty">{error}</p>
      </div>
    );
  }

  return (
    <div className="prediction-view">
      <div className="prediction-header">
        <h2>Prediction</h2>
        <button onClick={onClose} className="close-btn">&times;</button>
      </div>

      <span className="prediction-method">graph_math / 12w projection</span>

      {scenarios.map((s) => (
        <div key={s.type} className="scenario-card" style={{ borderLeftColor: typeColors[s.type] || "#888" }}>
          <div className="scenario-top">
            <span className="scenario-type" style={{ color: typeColors[s.type] }}>
              {typeLabels[s.type] || s.type}
            </span>
            <span className="scenario-prob" style={{ color: typeColors[s.type] }}>
              {s.probability}%
            </span>
          </div>
          {s.title && <h3 className="scenario-title">{s.title}</h3>}
          {s.narrative && <p className="scenario-narrative">{s.narrative}</p>}
          <div className="scenario-scores">
            <span>{s.total_score_initial}</span>
            <span className="scenario-arrow">&rarr; {s.total_delta >= 0 ? "+" : ""}{s.total_delta}</span>
            <span>&rarr; {s.total_score_final}</span>
          </div>
        </div>
      ))}

      {leveragePoint && (
        <div className="insight-card leverage">
          <span className="insight-label">Ключевой рычаг</span>
          <p>{leveragePoint}</p>
        </div>
      )}

      {warning && (
        <div className="insight-card warning">
          <span className="insight-label">Сигнал тревоги</span>
          <p>{warning}</p>
        </div>
      )}
    </div>
  );
}

// ── Main Dashboard ──────────────────────────────────────

export default function Dashboard({ userId, onOpenCheckin }: DashboardProps) {
  const [total, setTotal] = useState(0);
  const [spheres, setSpheres] = useState<SphereScore[]>([]);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPrediction, setShowPrediction] = useState(false);

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
        setNodes(graphRes.data.nodes || []);
        setEdges(graphRes.data.edges || []);
      }
      setLoading(false);
    }
    load();
  }, [userId]);

  if (loading) {
    return (
      <div className="dashboard">
        <div className="prediction-loading">
          <div className="spinner" />
          <p>Загружаю...</p>
        </div>
      </div>
    );
  }

  if (showPrediction) {
    return <PredictionView userId={userId} onClose={() => setShowPrediction(false)} />;
  }

  // Score color: green if high, purple if mid, red if low
  const scoreColor = total >= 60 ? "#22c55e" : total >= 40 ? "#818cf8" : "#ef4444";

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h1>Runa</h1>
        <div className="header-buttons">
          <button className="prediction-btn" onClick={() => setShowPrediction(true)}>
            Prediction
          </button>
          <button className="checkin-btn" onClick={onOpenCheckin}>
            Чекин
          </button>
        </div>
      </div>

      {/* Life Score */}
      <div className="life-score-card">
        <div className="score-number" style={{
          background: `linear-gradient(135deg, ${scoreColor}, ${scoreColor}aa)`,
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}>
          {Math.round(total)}
        </div>
        <div className="score-label">Life Score</div>
      </div>

      {/* Spheres */}
      <div className="spheres">
        <div className="section-title">Сферы жизни</div>
        {spheres.length === 0 && <p className="empty">Пройди онбординг</p>}
        {spheres.map((s) => {
          const barColor = s.score >= 60 ? "#22c55e" : s.score >= 40 ? "#6366f1" : "#ef4444";
          return (
            <div key={s.sphere} className="sphere-row">
              <div className="sphere-info">
                <span className="sphere-name">{s.sphere}</span>
                <span className="sphere-score" style={{ color: barColor }}>
                  {Math.round(s.score)}
                  {s.delta !== 0 && (
                    <span className={`sphere-delta ${s.delta > 0 ? "positive" : "negative"}`}>
                      {s.delta > 0 ? "+" : ""}{s.delta.toFixed(1)}
                    </span>
                  )}
                </span>
              </div>
              <div className="sphere-bar">
                <div className="sphere-fill" style={{ width: `${s.score}%`, background: barColor }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Visual Graph */}
      <div className="graph-section">
        <div className="graph-header">
          <div className="section-title" style={{ marginBottom: 0 }}>Граф личности</div>
          <div className="graph-stats">
            <span>{nodes.filter((n) => n.label !== "CheckIn" && n.label !== "Person").length} узлов</span>
            <span>{edges.filter((e) => e.type !== "CHANGED_ON").length} связей</span>
          </div>
        </div>
        {nodes.length === 0 ? (
          <p className="empty">Граф пока пуст</p>
        ) : (
          <>
            <VisualGraph nodes={nodes} edges={edges} />
            <div className="graph-legend">
              {Object.entries(NODE_COLORS).map(([label, color]) => (
                <span key={label} className="legend-item">
                  <span className="legend-dot" style={{ background: color }} />
                  {NODE_LABELS_RU[label] || label}
                </span>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
