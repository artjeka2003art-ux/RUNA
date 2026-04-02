import { useState, useEffect } from "react";
import { getSpheres, createSphere, renameSphere, deleteSphere } from "./api";

interface SphereVM {
  id: string;
  name: string;
  description: string;
  score: number | null;
  archived: boolean;
}

interface LifeMapProps {
  userId: string;
  onOpenSphere: (sphereId: string) => void;
}

export default function LifeMap({ userId, onOpenSphere }: LifeMapProps) {
  const [spheres, setSpheres] = useState<SphereVM[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    load();
  }, [userId]);

  async function load() {
    setLoading(true);
    const res = await getSpheres(userId);
    if (res.success) {
      setSpheres(res.data.spheres || []);
    }
    setLoading(false);
  }

  async function handleAdd() {
    const name = newName.trim();
    if (!name || actionLoading) return;
    setActionLoading(true);
    const res = await createSphere(userId, name);
    if (res.success) {
      setSpheres((prev) => [...prev, res.data.sphere]);
      setNewName("");
      setAdding(false);
    }
    setActionLoading(false);
  }

  async function handleRename(sphereId: string) {
    const name = renameValue.trim();
    if (!name || actionLoading) return;
    setActionLoading(true);
    const res = await renameSphere(userId, sphereId, name);
    if (res.success) {
      setSpheres((prev) =>
        prev.map((s) => (s.id === sphereId ? { ...s, name: res.data.sphere.name } : s))
      );
      setRenamingId(null);
    }
    setActionLoading(false);
  }

  async function handleDelete(sphereId: string, sphereName: string) {
    if (!confirm(`Удалить сферу "${sphereName}"?`)) return;
    setActionLoading(true);
    const res = await deleteSphere(userId, sphereId);
    if (res.success) {
      setSpheres((prev) => prev.filter((s) => s.id !== sphereId));
    }
    setActionLoading(false);
  }

  if (loading) {
    return (
      <div className="lifemap">
        <div className="today-loading"><div className="spinner" /></div>
      </div>
    );
  }

  const count = spheres.length;
  const angleStep = count > 0 ? (2 * Math.PI) / count : 0;
  const radius = Math.min(160, 110 + count * 7);

  function scoreColor(s: number | null): string {
    if (s == null) return "#52525b";
    if (s >= 65) return "#22c55e";
    if (s >= 45) return "#a78bfa";
    if (s >= 30) return "#f59e0b";
    return "#ef4444";
  }

  return (
    <div className="lifemap">
      <div className="lifemap-header">
        <h2>Life Map</h2>
        <p className="lifemap-subtitle">Твоя карта жизни. Нажми на сферу, чтобы открыть её.</p>
      </div>

      {/* Constellation layout */}
      <div className="lifemap-constellation">
        <div className="lifemap-center-label">Ты</div>

        {spheres.map((s, i) => {
          const angle = angleStep * i - Math.PI / 2;
          const x = Math.cos(angle) * radius;
          const y = Math.sin(angle) * radius;
          const color = scoreColor(s.score);

          return (
            <div
              key={s.id}
              className="lifemap-sphere"
              style={{ transform: `translate(${x}px, ${y}px)` }}
            >
              {/* Connection line */}
              <svg className="lifemap-line" viewBox="-2 -2 4 4" style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                width: `${Math.sqrt(x*x + y*y) * 2}px`,
                height: "4px",
                transform: `translate(-50%, -50%) rotate(${Math.atan2(-y, -x)}rad)`,
                overflow: "visible",
                pointerEvents: "none",
              }}>
              </svg>

              <button
                className="lifemap-sphere-btn"
                onClick={() => onOpenSphere(s.id)}
                style={{ borderColor: `${color}33` }}
              >
                <span className="lifemap-sphere-name">{s.name}</span>
                {s.score != null && (
                  <span className="lifemap-sphere-score" style={{ color }}>
                    {Math.round(s.score)}
                  </span>
                )}
              </button>

              {/* Quick actions */}
              <div className="lifemap-sphere-actions">
                <button
                  className="lifemap-action-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setRenamingId(s.id);
                    setRenameValue(s.name);
                  }}
                  title="Переименовать"
                >
                  &#x270E;
                </button>
                <button
                  className="lifemap-action-btn lifemap-action-delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(s.id, s.name);
                  }}
                  title="Удалить"
                >
                  &times;
                </button>
              </div>

              {/* Rename inline */}
              {renamingId === s.id && (
                <div className="lifemap-rename-popup">
                  <input
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleRename(s.id);
                      if (e.key === "Escape") setRenamingId(null);
                    }}
                    autoFocus
                  />
                  <button onClick={() => handleRename(s.id)} disabled={actionLoading}>OK</button>
                  <button onClick={() => setRenamingId(null)}>&#x2715;</button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Add sphere */}
      <div className="lifemap-add-area">
        {adding ? (
          <div className="lifemap-add-form">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAdd();
                if (e.key === "Escape") setAdding(false);
              }}
              placeholder="Название новой сферы..."
              autoFocus
            />
            <button onClick={handleAdd} disabled={actionLoading || !newName.trim()}>
              Добавить
            </button>
            <button onClick={() => setAdding(false)}>Отмена</button>
          </div>
        ) : (
          <button className="lifemap-add-btn" onClick={() => setAdding(true)}>
            + Добавить сферу
          </button>
        )}
      </div>
    </div>
  );
}
