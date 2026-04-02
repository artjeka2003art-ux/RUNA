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

export default function Chat({ userId, mode, onComplete }: ChatProps) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (mode === "onboarding" && messages.length === 0) {
      setLoading(true);
      startOnboarding(userId).then((res) => {
        if (res.success) {
          setSessionId(res.data.session_id);
          setMessages([{ role: "assistant", text: res.data.reply }]);
        }
        setLoading(false);
      });
    }
  }, [mode, userId]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);

    try {
      if (mode === "onboarding") {
        const res = await sendOnboardingMessage(userId, sessionId, text);
        if (res.success) {
          setMessages((m) => [...m, { role: "assistant", text: res.data.reply }]);
          if (res.data.completed) {
            const reveal: RevealData | undefined = res.data.spheres
              ? {
                  spheres: res.data.spheres,
                  lifeScore: res.data.life_score ?? 0,
                }
              : undefined;
            setTimeout(() => onComplete(reveal), 2000);
          }
        }
      } else {
        const res = await sendCheckinMessage(userId, text);
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

  return (
    <div className="chat">
      <div className="chat-header">
        {mode === "onboarding" ? (
          <>
            <h2>Знакомство</h2>
            <p className="chat-subtitle">Расскажи, что происходит в твоей жизни. Система начнёт строить твою модель.</p>
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
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={mode === "checkin" ? "Что сегодня происходит?" : "Расскажи..."}
          disabled={loading}
        />
        <button onClick={send} disabled={loading || !input.trim()}>&#x2191;</button>
      </div>
    </div>
  );
}
