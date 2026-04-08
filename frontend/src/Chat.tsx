import { useState, useRef, useEffect } from "react";
import { startOnboarding, sendOnboardingMessage, sendCheckinMessage } from "./api";
import { buildCheckinSummary, type CheckinSummaryVM } from "./mappers/checkin";
import type { RevealData } from "./App";

interface Msg {
  role: "user" | "assistant";
  text: string;
  summary?: CheckinSummaryVM;
}

interface ChatProps {
  userId: string;
  mode: "onboarding" | "checkin";
  onComplete: (data?: RevealData) => void;
}

const MIN_EXCHANGES_FOR_FINISH = 4;

export default function Chat({ userId, mode, onComplete }: ChatProps) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [exchangeCount, setExchangeCount] = useState(0);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (mode === "onboarding" && messages.length === 0) {
      setLoading(true);
      startOnboarding(userId).then((res) => {
        if (res.success) {
          setSessionId(res.data.session_id);
          setMessages([{ role: "assistant", text: res.data.reply }]);
          setExchangeCount(res.data.exchange_count ?? 1);
        }
        setLoading(false);
      });
    }
  }, [mode, userId]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(forceComplete = false) {
    const text = input.trim();
    if (loading) return;
    if (!forceComplete && !text) return;

    const userText = text || "Давай построим карту из того, что уже есть.";
    setInput("");
    setMessages((m) => [...m, { role: "user", text: userText }]);
    setLoading(true);

    try {
      if (mode === "onboarding") {
        const res = await sendOnboardingMessage(userId, sessionId, userText, forceComplete);
        if (res.success) {
          setExchangeCount(res.data.exchange_count ?? exchangeCount + 1);
          setMessages((m) => [...m, { role: "assistant", text: res.data.reply }]);
          if (res.data.completed) {
            const reveal: RevealData | undefined = res.data.spheres
              ? {
                  spheres: res.data.spheres,
                  lifeScore: res.data.life_score ?? 0,
                  activeTensions: res.data.active_tensions ?? [],
                  decisionBridge: res.data.decision_bridge ?? undefined,
                }
              : undefined;
            setTimeout(() => onComplete(reveal), 2000);
          }
        }
      } else {
        const res = await sendCheckinMessage(userId, userText);
        if (res.success) {
          const summary = buildCheckinSummary(res.data);
          setMessages((m) => [...m, { role: "assistant", text: res.data.reply, summary }]);
        }
      }
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "Что-то пошло не так. Попробуй ещё раз." }]);
    }
    setLoading(false);
  }

  const canFinishEarly = mode === "onboarding" && exchangeCount >= MIN_EXCHANGES_FOR_FINISH && !loading;

  // Progress: rough stage indicator for onboarding
  const progressLabel = mode === "onboarding"
    ? exchangeCount < 4
      ? "Знакомство"
      : exchangeCount < 8
        ? "Карта строится..."
        : "Почти готово"
    : null;

  return (
    <div className="chat">
      <div className="chat-header">
        {mode === "onboarding" ? (
          <>
            <h2>Построим карту твоей жизни</h2>
            <p className="chat-subtitle">
              Расскажи коротко о главных сферах — работа, отношения, здоровье, планы.
              Runa построит модель для прогнозов и сценариев.
            </p>
            {progressLabel && (
              <div className="onboarding-progress">
                <span className="onboarding-progress-dot" />
                <span className="onboarding-progress-label">{progressLabel}</span>
              </div>
            )}
          </>
        ) : (
          <>
            <h2>Check-in</h2>
            <p className="chat-subtitle">Что сегодня на поверхности? Говори как есть — система обновит твою картину.</p>
          </>
        )}
      </div>

      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.role === "assistant" && <span className="msg-avatar">R</span>}
            <div className="msg-bubble">
              {m.text}
              {m.summary && (
                <div className="checkin-summary">
                  <div className="summary-header">
                    Картина обновлена
                    {(m.summary.weightsUpdated > 0 || m.summary.nodesCreated > 0 || m.summary.resolved > 0) && (
                      <span className="summary-counts">
                        {[
                          m.summary.weightsUpdated > 0 && `${m.summary.weightsUpdated} связей`,
                          m.summary.nodesCreated > 0 && `${m.summary.nodesCreated} узлов`,
                          m.summary.resolved > 0 && `${m.summary.resolved} снято`,
                        ].filter(Boolean).join(" / ")}
                      </span>
                    )}
                  </div>

                  {m.summary.newScore != null && (
                    <div className="summary-score-block">
                      <span className="summary-score-value">{m.summary.newScore}</span>
                      <span className="summary-score-label">Life Score</span>
                      {m.summary.scoreDelta != null && m.summary.scoreDelta !== 0 && (
                        <span className="summary-score-delta" style={{ color: m.summary.scoreDelta > 0 ? "#22c55e" : "#ef4444" }}>
                          {m.summary.scoreDelta > 0 ? "+" : ""}{m.summary.scoreDelta}
                        </span>
                      )}
                    </div>
                  )}

                  {m.summary.updates.length > 0 && (
                    <div className="summary-section summary-up">
                      <span className="summary-label">Зафиксировано</span>
                      {m.summary.updates.map((t, j) => <span key={j} className="summary-item">{t}</span>)}
                    </div>
                  )}

                  {m.summary.concerns.length > 0 && (
                    <div className="summary-section summary-down">
                      <span className="summary-label">Система обратила внимание</span>
                      {m.summary.concerns.map((t, j) => <span key={j} className="summary-item">{t}</span>)}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="msg assistant">
            <span className="msg-avatar">R</span>
            <div className="msg-bubble msg-typing">...</div>
          </div>
        )}
        <div ref={bottom} />
      </div>

      <div className="chat-input-bar">
        {canFinishEarly && (
          <button
            className="onboarding-finish-btn"
            onClick={() => send(true)}
            title="Построить карту из того, что уже есть"
          >
            Построить карту
          </button>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={mode === "checkin" ? "Что сегодня происходит?" : "Расскажи..."}
          disabled={loading}
        />
        <button onClick={() => send()} disabled={loading || !input.trim()}>&#x2191;</button>
      </div>
    </div>
  );
}
