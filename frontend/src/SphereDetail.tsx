import { useState, useEffect, useRef } from "react";
import { getSphereDetail, sendSphereMessage, renameSphere, deleteSphere } from "./api";

interface RelatedNode {
  type: string;
  name: string;
  description: string;
  weight: number;
}

interface SphereData {
  id: string;
  name: string;
  description: string;
  score: number | null;
  related_blockers: RelatedNode[];
  related_goals: RelatedNode[];
  related_patterns: RelatedNode[];
  related_values: RelatedNode[];
  related_spheres: string[];
}

interface Msg {
  role: "user" | "assistant";
  text: string;
  graphUpdates?: { weights_updated: number; nodes_created: number; resolved: number };
}

interface SphereDetailProps {
  userId: string;
  sphereId: string;
  onBack: () => void;
}

export default function SphereDetail({ userId, sphereId, onBack }: SphereDetailProps) {
  const [sphere, setSphere] = useState<SphereData | null>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSphere();
  }, [userId, sphereId]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function loadSphere() {
    setLoading(true);
    const res = await getSphereDetail(userId, sphereId);
    if (res.success) {
      setSphere(res.data.sphere);
    }
    setLoading(false);
  }

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setSending(true);

    try {
      const res = await sendSphereMessage(userId, sphereId, text);
      if (res.success) {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            text: res.data.reply,
            graphUpdates: res.data.graph_updates,
          },
        ]);
        // Update sphere data with fresh info
        if (res.data.sphere) {
          setSphere((prev) => prev ? { ...prev, ...res.data.sphere } : prev);
        }
      }
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Что-то пошло не так. Попробуй ещё раз." },
      ]);
    }
    setSending(false);
  }

  async function handleRename() {
    const name = renameValue.trim();
    if (!name) return;
    const res = await renameSphere(userId, sphereId, name);
    if (res.success) {
      setSphere((prev) => prev ? { ...prev, name } : prev);
      setRenaming(false);
    }
  }

  async function handleDelete() {
    if (!sphere || !confirm(`Удалить сферу "${sphere.name}"?`)) return;
    const res = await deleteSphere(userId, sphereId);
    if (res.success) {
      onBack();
    }
  }

  if (loading || !sphere) {
    return (
      <div className="sphere-detail">
        <div className="today-loading"><div className="spinner" /></div>
      </div>
    );
  }

  function scoreColor(s: number | null): string {
    if (s == null) return "#52525b";
    if (s >= 65) return "#22c55e";
    if (s >= 45) return "#a78bfa";
    if (s >= 30) return "#f59e0b";
    return "#ef4444";
  }

  const typeLabels: Record<string, string> = {
    Blocker: "Блокеры",
    Goal: "Цели",
    Pattern: "Паттерны",
    Value: "Ценности",
  };

  const sections: { key: string; label: string; items: RelatedNode[]; accent: string }[] = [
    { key: "blockers", label: typeLabels.Blocker, items: sphere.related_blockers, accent: "#ef4444" },
    { key: "goals", label: typeLabels.Goal, items: sphere.related_goals, accent: "#22c55e" },
    { key: "patterns", label: typeLabels.Pattern, items: sphere.related_patterns, accent: "#a78bfa" },
    { key: "values", label: typeLabels.Value, items: sphere.related_values, accent: "#f59e0b" },
  ];

  return (
    <div className="sphere-detail">
      {/* Header */}
      <div className="sphere-detail-header">
        <button className="sphere-back-btn" onClick={onBack}>&larr; Life Map</button>
        <div className="sphere-detail-title-row">
          {renaming ? (
            <div className="sphere-rename-inline">
              <input
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleRename();
                  if (e.key === "Escape") setRenaming(false);
                }}
                autoFocus
              />
              <button onClick={handleRename}>OK</button>
              <button onClick={() => setRenaming(false)}>&#x2715;</button>
            </div>
          ) : (
            <h2 className="sphere-detail-name">{sphere.name}</h2>
          )}
          {sphere.score != null && (
            <span className="sphere-detail-score" style={{ color: scoreColor(sphere.score) }}>
              {Math.round(sphere.score)}
            </span>
          )}
        </div>
        {sphere.description && (
          <p className="sphere-detail-desc">{sphere.description}</p>
        )}
        <div className="sphere-detail-actions">
          <button
            className="sphere-action-small"
            onClick={() => { setRenaming(true); setRenameValue(sphere.name); }}
          >
            Переименовать
          </button>
          <button className="sphere-action-small sphere-action-danger" onClick={handleDelete}>
            Удалить
          </button>
        </div>
      </div>

      {/* Related entities */}
      <div className="sphere-detail-body">
        <div className="sphere-related-grid">
          {sections.map((sec) => (
            sec.items.length > 0 && (
              <div key={sec.key} className="sphere-related-section">
                <h4 className="sphere-related-title" style={{ color: sec.accent }}>{sec.label}</h4>
                {sec.items.map((item, i) => (
                  <div key={i} className="sphere-related-item">
                    <span className="sphere-related-name">{item.name}</span>
                    {item.description && (
                      <span className="sphere-related-desc">{item.description}</span>
                    )}
                  </div>
                ))}
              </div>
            )
          ))}
        </div>

        {sphere.related_spheres.length > 0 && (
          <div className="sphere-connections">
            <span className="sphere-connections-label">Связанные сферы:</span>
            {sphere.related_spheres.map((name) => (
              <span key={name} className="sphere-connection-chip">{name}</span>
            ))}
          </div>
        )}

        {/* Sphere Chat */}
        <div className="sphere-chat">
          <h3 className="sphere-chat-title">Разговор о сфере</h3>

          {messages.length === 0 && (
            <p className="sphere-chat-hint">
              Расскажи, что происходит в этой сфере. AI знает её контекст и обновит всю модель.
            </p>
          )}

          <div className="sphere-chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                {m.role === "assistant" && <span className="msg-avatar">R</span>}
                <div className="msg-bubble">
                  {m.text}
                  {m.graphUpdates && (m.graphUpdates.weights_updated > 0 || m.graphUpdates.nodes_created > 0) && (
                    <div className="sphere-chat-updates">
                      Граф обновлён:
                      {m.graphUpdates.weights_updated > 0 && ` ${m.graphUpdates.weights_updated} связей`}
                      {m.graphUpdates.nodes_created > 0 && ` ${m.graphUpdates.nodes_created} узлов`}
                      {m.graphUpdates.resolved > 0 && ` ${m.graphUpdates.resolved} снято`}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="msg assistant">
                <span className="msg-avatar">R</span>
                <div className="msg-bubble msg-typing">...</div>
              </div>
            )}
            <div ref={bottom} />
          </div>

          <div className="chat-input-bar">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder={`Что происходит в "${sphere.name}"?`}
              disabled={sending}
            />
            <button onClick={send} disabled={sending || !input.trim()}>&#x2191;</button>
          </div>
        </div>
      </div>
    </div>
  );
}
