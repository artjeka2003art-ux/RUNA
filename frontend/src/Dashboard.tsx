import { useState, useEffect } from "react";
import { getLifeScore, getGraph } from "./api";

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

interface DashboardProps {
  userId: string;
  onOpenCheckin: () => void;
}

export default function Dashboard({ userId, onOpenCheckin }: DashboardProps) {
  const [total, setTotal] = useState(0);
  const [spheres, setSpheres] = useState<SphereScore[]>([]);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
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
        setNodes(graphRes.data.nodes || []);
        setEdges(graphRes.data.edges || []);
      }
      setLoading(false);
    }
    load();
  }, [userId]);

  if (loading) {
    return <div className="dashboard"><p>Загружаю данные...</p></div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Runa</h1>
        <button className="checkin-btn" onClick={onOpenCheckin}>
          Чекин
        </button>
      </div>

      {/* Life Score */}
      <div className="life-score-card">
        <div className="score-number">{Math.round(total)}</div>
        <div className="score-label">Life Score</div>
      </div>

      {/* Spheres */}
      <div className="spheres">
        <h3>Сферы жизни</h3>
        {spheres.length === 0 && <p className="empty">Пройди онбординг чтобы увидеть сферы</p>}
        {spheres.map((s) => (
          <div key={s.sphere} className="sphere-row">
            <div className="sphere-info">
              <span className="sphere-name">{s.sphere}</span>
              <span className="sphere-score">{Math.round(s.score)}</span>
            </div>
            <div className="sphere-bar">
              <div
                className="sphere-fill"
                style={{ width: `${s.score}%` }}
              />
            </div>
            {s.reason && <span className="sphere-reason">{s.reason}</span>}
          </div>
        ))}
      </div>

      {/* Graph */}
      <div className="graph-section">
        <h3>Граф личности</h3>
        {nodes.length === 0 ? (
          <p className="empty">Граф пока пуст</p>
        ) : (
          <div className="graph-stats">
            <span>{nodes.length} узлов</span>
            <span>{edges.length} связей</span>
          </div>
        )}
        <div className="graph-nodes">
          {nodes.map((n, i) => (
            <span key={i} className={`node-tag ${n.label.toLowerCase()}`}>
              {n.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
