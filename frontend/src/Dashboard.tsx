import { useState, useEffect } from "react";
import { getLifeScore, getGraph, getScenarios } from "./api";

interface SphereScore { sphere: string; score: number; delta: number; reason: string; }
interface GraphNode { label: string; name: string; }
interface GraphEdge { from: string; to: string; type: string; weight: number; }

const SPHERE_ICONS = ["◆", "●", "▲", "■", "★", "◯"];

function scoreColor(s: number): string {
  if (s >= 65) return "#22c55e";
  if (s >= 45) return "#a78bfa";
  if (s >= 30) return "#f59e0b";
  return "#ef4444";
}

const NODE_COLORS: Record<string, string> = {
  Sphere: "#a78bfa", Blocker: "#ef4444", Pattern: "#f59e0b",
  Goal: "#22c55e", Value: "#c084fc", Event: "#38bdf8",
};

export default function Dashboard({ userId }: { userId: string }) {
  const [total, setTotal] = useState(0);
  const [spheres, setSpheres] = useState<SphereScore[]>([]);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [blockers, setBlockers] = useState<GraphNode[]>([]);
  const [goals, setGoals] = useState<GraphNode[]>([]);
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
        const e = (graphRes.data.edges || []).filter((x: GraphEdge) => x.type !== "CHANGED_ON");
        setNodes(n);
        setEdges(e);
        setBlockers(n.filter((x: GraphNode) => x.label === "Blocker"));
        setGoals(n.filter((x: GraphNode) => x.label === "Goal"));
      }
      // Try loading prediction preview (non-blocking)
      getScenarios(userId).then((r) => {
        if (r.success && r.data.scenarios?.length) setPrediction(r.data);
      }).catch(() => {});
      setLoading(false);
    }
    load();
  }, [userId]);

  if (loading) {
    return <div className="dash"><div className="pred-loading"><div className="spinner" /></div></div>;
  }

  const color = scoreColor(total);
  const R = 85;
  const C = 2 * Math.PI * R;
  const offset = C - (total / 100) * C;

  const today = new Date().toLocaleDateString("ru-RU", { weekday: "long", day: "numeric", month: "long" });

  // Mini graph positions
  const W = 360, H = 260, CX = W / 2, CY = H / 2;
  const visNodes = nodes.filter((n) => n.label !== "CheckIn" && n.label !== "Person");
  const sphNodes = visNodes.filter((n) => n.label === "Sphere");
  const othNodes = visNodes.filter((n) => n.label !== "Sphere");
  const pos: Record<string, { x: number; y: number }> = {};
  sphNodes.forEach((n, i) => {
    const a = (i / Math.max(sphNodes.length, 1)) * Math.PI * 2 - Math.PI / 2;
    pos[n.name] = { x: CX + Math.cos(a) * 65, y: CY + Math.sin(a) * 55 };
  });
  othNodes.forEach((n, i) => {
    const edge = edges.find((e) => e.from === n.name && pos[e.to]);
    if (edge && pos[edge.to]) {
      const sp = pos[edge.to];
      const ang = Math.atan2(sp.y - CY, sp.x - CX);
      const spread = ((i % 3) - 1) * 0.5;
      pos[n.name] = { x: CX + Math.cos(ang + spread) * 110, y: CY + Math.sin(ang + spread) * 95 };
    } else {
      const a = (i / Math.max(othNodes.length, 1)) * Math.PI * 2 - Math.PI / 2;
      pos[n.name] = { x: CX + Math.cos(a) * 110, y: CY + Math.sin(a) * 95 };
    }
  });
  const visEdges = edges.filter((e) => pos[e.from] && pos[e.to]);

  return (
    <div className="dash">
      <div className="dash-head">
        <span className="dash-logo">Runa</span>
        <span className="dash-date">{today}</span>
      </div>

      {/* Row 1: Score + Spheres */}
      <div className="dash-row">
        {/* Score Ring */}
        <div className="dash-card score-card">
          <div className="score-ring-container">
            <svg className="score-ring-svg" viewBox="0 0 200 200">
              <circle className="score-ring-bg" cx="100" cy="100" r={R} />
              <circle className="score-ring-fill" cx="100" cy="100" r={R} stroke={color} strokeDasharray={C} strokeDashoffset={offset} />
            </svg>
            <div className="score-ring-center">
              <span className="score-ring-number" style={{ color }}>{Math.round(total)}</span>
              <span className="score-ring-label">Life Score</span>
            </div>
          </div>
          <div className="score-meta">
            <div className="score-meta-row">
              <span className="meta-val">{spheres.length}</span><span className="meta-lbl">сфер</span>
            </div>
            <div className="score-meta-row">
              <span className="meta-val">{nodes.length}</span><span className="meta-lbl">узлов</span>
            </div>
            <div className="score-meta-row">
              <span className="meta-val">{edges.length}</span><span className="meta-lbl">связей</span>
            </div>
          </div>
        </div>

        {/* Spheres list */}
        <div className="dash-card spheres-card">
          <div className="card-title">Сферы жизни</div>
          {spheres.map((s, i) => {
            const c = scoreColor(s.score);
            return (
              <div key={s.sphere} className="sphere-row-mini">
                <span className="sphere-dot" style={{ background: c }}>{SPHERE_ICONS[i % SPHERE_ICONS.length]}</span>
                <span className="sphere-name-m">{s.sphere}</span>
                <div className="sphere-bar-m"><div className="sphere-bar-fill-m" style={{ width: `${s.score}%`, background: c }} /></div>
                <span className="sphere-num-m" style={{ color: c }}>{Math.round(s.score)}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Row 2: Mini Graph + Insights */}
      <div className="dash-row">
        {/* Mini Graph */}
        <div className="dash-card graph-card">
          <div className="card-title">Граф личности</div>
          <svg viewBox={`0 0 ${W} ${H}`} className="mini-graph-svg">
            <defs>
              <radialGradient id="mg"><stop offset="0%" stopColor="#7c3aed" stopOpacity="0.04" /><stop offset="100%" stopColor="transparent" /></radialGradient>
            </defs>
            <circle cx={CX} cy={CY} r={120} fill="url(#mg)" />
            {visEdges.map((e, i) => {
              const f = pos[e.from], t = pos[e.to];
              const fn = visNodes.find((n) => n.name === e.from);
              const ec = fn?.label === "Blocker" ? "rgba(239,68,68,0.3)" : fn?.label === "Goal" ? "rgba(34,197,94,0.3)" : "rgba(167,139,250,0.12)";
              return <line key={i} x1={f.x} y1={f.y} x2={t.x} y2={t.y} stroke={ec} strokeWidth={Math.max(0.5, e.weight * 1.5)} />;
            })}
            {visNodes.map((n) => {
              const p = pos[n.name]; if (!p) return null;
              const c = NODE_COLORS[n.label] || "#666";
              const isSp = n.label === "Sphere";
              const r = isSp ? 22 : 14;
              const nm = n.name.length > 10 ? n.name.slice(0, 9) + ".." : n.name;
              return (
                <g key={n.name}>
                  {isSp && <circle cx={p.x} cy={p.y} r={r + 5} fill={c} opacity={0.05} />}
                  <circle cx={p.x} cy={p.y} r={r} fill={`${c}18`} stroke={c} strokeWidth={isSp ? 1.5 : 0.8} strokeOpacity={isSp ? 0.7 : 0.4} />
                  <text x={p.x} y={p.y + 1} textAnchor="middle" dominantBaseline="central" fill={c} fontSize={isSp ? 7 : 5.5} fontWeight={isSp ? 600 : 400}>{nm}</text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Insights */}
        <div className="dash-card insights-card">
          <div className="card-title">Инсайты</div>

          {/* Blockers */}
          {blockers.length > 0 && (
            <div className="insight-block">
              <div className="insight-head red">Блокеры ({blockers.length})</div>
              {blockers.map((b) => (
                <div key={b.name} className="insight-item red">{b.name}</div>
              ))}
            </div>
          )}

          {/* Goals */}
          {goals.length > 0 && (
            <div className="insight-block">
              <div className="insight-head green">Цели ({goals.length})</div>
              {goals.map((g) => (
                <div key={g.name} className="insight-item green">{g.name}</div>
              ))}
            </div>
          )}

          {/* Prediction preview */}
          {prediction?.scenarios?.map((s: any) => (
            <div key={s.type} className="pred-mini">
              <span className="pred-mini-type" style={{ color: s.type === "optimistic" ? "#22c55e" : s.type === "pessimistic" ? "#ef4444" : "#a78bfa" }}>
                {s.type === "optimistic" ? "Опт." : s.type === "pessimistic" ? "Пес." : "Реал."}
              </span>
              <div className="pred-mini-bar">
                <div className="pred-mini-fill" style={{
                  width: `${s.probability}%`,
                  background: s.type === "optimistic" ? "#22c55e" : s.type === "pessimistic" ? "#ef4444" : "#a78bfa"
                }} />
              </div>
              <span className="pred-mini-pct">{s.probability}%</span>
            </div>
          ))}

          {!prediction && blockers.length === 0 && goals.length === 0 && (
            <p className="empty-state" style={{ padding: "20px 0" }}>Делай чекины — инсайты появятся</p>
          )}
        </div>
      </div>
    </div>
  );
}
