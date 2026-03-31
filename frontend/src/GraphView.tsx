import { useState, useEffect } from "react";
import { getGraph } from "./api";

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

const COLORS: Record<string, string> = {
  Sphere: "#a78bfa",
  Blocker: "#ef4444",
  Pattern: "#f59e0b",
  Goal: "#22c55e",
  Value: "#c084fc",
  Event: "#38bdf8",
};

const LABELS_RU: Record<string, string> = {
  Sphere: "Сфера",
  Blocker: "Блокер",
  Pattern: "Паттерн",
  Goal: "Цель",
  Value: "Ценность",
  Event: "Событие",
};

export default function GraphView({ userId }: { userId: string }) {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getGraph(userId).then((res) => {
      if (res.success) {
        setNodes((res.data.nodes || []).filter(
          (n: GraphNode) => n.label !== "CheckIn" && n.label !== "Person"
        ));
        setEdges((res.data.edges || []).filter(
          (e: GraphEdge) => e.type !== "CHANGED_ON"
        ));
      }
      setLoading(false);
    });
  }, [userId]);

  if (loading) {
    return <div className="graph-view"><div className="pred-loading"><div className="spinner" /></div></div>;
  }

  const W = 800;
  const H = 600;
  const CX = W / 2;
  const CY = H / 2;

  const spheres = nodes.filter((n) => n.label === "Sphere");
  const others = nodes.filter((n) => n.label !== "Sphere");
  const pos: Record<string, { x: number; y: number }> = {};

  spheres.forEach((n, i) => {
    const a = (i / Math.max(spheres.length, 1)) * Math.PI * 2 - Math.PI / 2;
    pos[n.name] = { x: CX + Math.cos(a) * 140, y: CY + Math.sin(a) * 130 };
  });

  others.forEach((n, i) => {
    const edge = edges.find((e) => e.from === n.name && pos[e.to]);
    if (edge && pos[edge.to]) {
      const sp = pos[edge.to];
      const ang = Math.atan2(sp.y - CY, sp.x - CX);
      const spread = ((i % 4) - 1.5) * 0.45;
      pos[n.name] = {
        x: CX + Math.cos(ang + spread) * 250,
        y: CY + Math.sin(ang + spread) * 230,
      };
    } else {
      const a = (i / Math.max(others.length, 1)) * Math.PI * 2 - Math.PI / 2;
      pos[n.name] = { x: CX + Math.cos(a) * 250, y: CY + Math.sin(a) * 230 };
    }
  });

  const visEdges = edges.filter((e) => pos[e.from] && pos[e.to]);

  return (
    <div className="graph-view">
      <h2>Граф личности</h2>
      <div className="graph-canvas">
        <svg viewBox={`0 0 ${W} ${H}`} className="graph-svg">
          <defs>
            <radialGradient id="glow">
              <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.05" />
              <stop offset="100%" stopColor="transparent" stopOpacity="0" />
            </radialGradient>
          </defs>
          <circle cx={CX} cy={CY} r={280} fill="url(#glow)" />

          {visEdges.map((e, i) => {
            const f = pos[e.from];
            const t = pos[e.to];
            const fromNode = nodes.find((n) => n.name === e.from);
            const c = fromNode?.label === "Blocker" ? "rgba(239,68,68,0.35)" :
                      fromNode?.label === "Goal" ? "rgba(34,197,94,0.35)" :
                      "rgba(167,139,250,0.15)";
            return <line key={i} x1={f.x} y1={f.y} x2={t.x} y2={t.y} stroke={c} strokeWidth={Math.max(0.5, e.weight * 2)} />;
          })}

          {nodes.map((n) => {
            const p = pos[n.name];
            if (!p) return null;
            const c = COLORS[n.label] || "#666";
            const isSphere = n.label === "Sphere";
            const r = isSphere ? 34 : 24;
            const name = n.name.length > 13 ? n.name.slice(0, 12) + ".." : n.name;

            return (
              <g key={n.name}>
                {isSphere && <circle cx={p.x} cy={p.y} r={r + 10} fill={c} opacity={0.04} />}
                <circle cx={p.x} cy={p.y} r={r}
                  fill={isSphere ? `${c}20` : `${c}10`}
                  stroke={c}
                  strokeWidth={isSphere ? 2 : 1}
                  strokeOpacity={isSphere ? 0.8 : 0.5}
                />
                <text x={p.x} y={p.y + 1} textAnchor="middle" dominantBaseline="central"
                  fill={c} fontSize={isSphere ? 10 : 8} fontWeight={isSphere ? 600 : 500}
                >{name}</text>
              </g>
            );
          })}
        </svg>
      </div>
      <div className="graph-legend">
        {Object.entries(COLORS).map(([k, c]) => (
          <span key={k} className="legend-chip">
            <span className="legend-dot" style={{ background: c }} />
            {LABELS_RU[k] || k}
          </span>
        ))}
      </div>
    </div>
  );
}
