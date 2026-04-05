import { useState, useEffect, useRef } from "react";
import {
  getSphereDetail,
  sendSphereMessage,
  renameSphere,
  deleteSphere,
  getSphereDocuments,
  uploadSphereDocument,
  deleteSphereDocument,
  type SphereDocument,
} from "./api";

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

interface WorkspaceSphereContext {
  missingWhat: string;
  missingWhy: string;
}

interface SphereDetailProps {
  userId: string;
  sphereId: string;
  intro?: string | null;
  onBack: () => void;
  workspaceContext?: WorkspaceSphereContext | null;
}

export default function SphereDetail({ userId, sphereId, intro, onBack, workspaceContext }: SphereDetailProps) {
  const [sphere, setSphere] = useState<SphereData | null>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<Msg[]>(() =>
    intro ? [{ role: "assistant" as const, text: intro }] : []
  );
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [docs, setDocs] = useState<SphereDocument[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSphere();
    loadDocs();
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
        if (res.data.sphere) {
          setSphere((prev) => prev ? { ...prev, ...res.data.sphere } : prev);
        }
        // Reload full detail to see updated related nodes
        loadSphere();
      }
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Что-то пошло не так. Попробуй ещё раз." },
      ]);
    }
    setSending(false);
  }

  async function loadDocs() {
    const res = await getSphereDocuments(userId, sphereId);
    if (res.success && res.data?.documents) {
      setDocs(res.data.documents);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await uploadSphereDocument(userId, sphereId, file);
      if (res.success) {
        await loadDocs();
      }
    } catch { /* ignore */ }
    setUploading(false);
    if (fileInput.current) fileInput.current.value = "";
  }

  async function handleDeleteDoc(docId: string) {
    const res = await deleteSphereDocument(userId, sphereId, docId);
    if (res.success) {
      setDocs((d) => d.filter((doc) => doc.id !== docId));
    }
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

  const blockers = sphere.related_blockers;
  const goals = sphere.related_goals;
  const patterns = sphere.related_patterns;
  const values = sphere.related_values;
  const hasRelated = blockers.length + goals.length + patterns.length + values.length > 0;

  // Build "what's happening" summary
  const pressureItems = blockers.filter((b) => b.weight >= 0.5);
  const growthItems = [...goals, ...values].filter((g) => g.weight >= 0.4);

  return (
    <div className="sphere-detail">
      {/* Workspace context banner */}
      {workspaceContext && (
        <div className="sphere-ws-banner">
          <div className="sphere-ws-banner-label">Из Decision Workspace</div>
          <div className="sphere-ws-banner-what">
            Нужно добавить: <strong>{workspaceContext.missingWhat}</strong>
          </div>
          <div className="sphere-ws-banner-why">{workspaceContext.missingWhy}</div>
          <button className="sphere-ws-banner-back" onClick={onBack}>
            &larr; Вернуться в Workspace
          </button>
        </div>
      )}

      {/* Header */}
      <div className="sphere-detail-header">
        <button className="sphere-back-btn" onClick={onBack}>
          &larr; {workspaceContext ? "Decision Workspace" : "Life Map"}
        </button>

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
        {!sphere.description && (
          <p className="sphere-detail-desc sphere-detail-desc-empty">
            Начни разговор ниже — Runa опишет смысл этой сферы.
          </p>
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

      <div className="sphere-detail-body">
        {/* Summary block: What's happening now */}
        {hasRelated && (
          <div className="sphere-summary-block">
            {/* What's holding back */}
            {pressureItems.length > 0 && (
              <div className="sphere-summary-section sphere-summary-pressure">
                <h4 className="sphere-summary-label">Что давит</h4>
                {pressureItems.map((b, i) => (
                  <div key={i} className="sphere-summary-item">
                    <span className="sphere-summary-name">{b.name}</span>
                    {b.description && <span className="sphere-summary-desc">{b.description}</span>}
                  </div>
                ))}
              </div>
            )}

            {/* Where growth is */}
            {growthItems.length > 0 && (
              <div className="sphere-summary-section sphere-summary-growth">
                <h4 className="sphere-summary-label">На что можно опереться</h4>
                {growthItems.map((g, i) => (
                  <div key={i} className="sphere-summary-item">
                    <span className="sphere-summary-name">{g.name}</span>
                    {g.description && <span className="sphere-summary-desc">{g.description}</span>}
                  </div>
                ))}
              </div>
            )}

            {/* Patterns noticed */}
            {patterns.length > 0 && (
              <div className="sphere-summary-section sphere-summary-patterns">
                <h4 className="sphere-summary-label">Замеченные паттерны</h4>
                {patterns.map((p, i) => (
                  <div key={i} className="sphere-summary-item">
                    <span className="sphere-summary-name">{p.name}</span>
                    {p.description && <span className="sphere-summary-desc">{p.description}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Connected spheres */}
        {sphere.related_spheres.length > 0 && (
          <div className="sphere-connections">
            <span className="sphere-connections-label">Связана с:</span>
            {sphere.related_spheres.map((name) => (
              <span key={name} className="sphere-connection-chip">{name}</span>
            ))}
          </div>
        )}

        {/* Empty state — no related entities yet */}
        {!hasRelated && !intro && (
          <div className="sphere-empty-state">
            <p>Эта сфера пока пуста. Расскажи о ней в чате ниже — Runa начнёт строить картину.</p>
          </div>
        )}

        {/* Documents */}
        <div className="sphere-docs">
          <div className="sphere-docs-header">
            <h3 className="sphere-docs-title">Документы</h3>
            <label className={`sphere-docs-upload-btn${uploading ? " disabled" : ""}`}>
              {uploading ? "Загрузка..." : "+ Добавить"}
              <input
                ref={fileInput}
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleUpload}
                disabled={uploading}
                hidden
              />
            </label>
          </div>
          {docs.length === 0 ? (
            <p className="sphere-docs-hint">
              Добавь документы (резюме, оффер, контракт, бюджет) — это усилит точность прогноза. Необязательно.
            </p>
          ) : (
            <div className="sphere-docs-list">
              {docs.map((d) => (
                <div key={d.id} className="sphere-doc-item">
                  <span className="sphere-doc-name">{d.filename}</span>
                  <span className={`sphere-doc-status sphere-doc-status-${d.status}`}>
                    {d.status === "processed" ? "Обработан" :
                     d.status === "limited" ? "Частично" :
                     d.status === "failed" ? "Ошибка" : d.status}
                  </span>
                  <button className="sphere-doc-delete" onClick={() => handleDeleteDoc(d.id)} title="Удалить">
                    &times;
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sphere Chat */}
        <div className="sphere-chat">
          <h3 className="sphere-chat-title">
            {messages.length === 0 ? "Начни разговор" : "Разговор"}
          </h3>

          {messages.length === 0 && (
            <p className="sphere-chat-hint">
              Расскажи, что для тебя значит эта сфера. Что в ней происходит сейчас? Что хочешь изменить?
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
                      Модель обновлена
                      {m.graphUpdates.weights_updated > 0 && ` · ${m.graphUpdates.weights_updated} связей`}
                      {m.graphUpdates.nodes_created > 0 && ` · ${m.graphUpdates.nodes_created} новых узлов`}
                      {m.graphUpdates.resolved > 0 && ` · ${m.graphUpdates.resolved} снято`}
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
