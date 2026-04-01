import { useState, useRef, useEffect } from "react";
import { startOnboarding, sendOnboardingMessage, sendCheckinMessage } from "./api";

interface Msg {
  role: "user" | "assistant";
  text: string;
  summary?: CheckinSummary;
}

interface CheckinSummary {
  improved: string[];
  declined: string[];
  scoreDelta: number | null;
  newScore: number | null;
}

interface ChatProps {
  userId: string;
  mode: "onboarding" | "checkin";
  onComplete: () => void;
}

function parseCheckinSummary(data: any): CheckinSummary | undefined {
  const upd = data.graph_updates;
  const score = data.life_score;
  if (!upd && !score) return undefined;

  const improved: string[] = [];
  const declined: string[] = [];

  if (upd?.details) {
    for (const d of upd.details) {
      const text = String(d);
      if (/добав|созда|нов|goal|value|support/i.test(text)) improved.push(text);
      else if (/blocker|блок|снижен|упал/i.test(text)) declined.push(text);
      else improved.push(text);
    }
  }

  return {
    improved: improved.slice(0, 3),
    declined: declined.slice(0, 2),
    scoreDelta: score?.delta ?? null,
    newScore: score?.total ?? null,
  };
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
          if (res.data.completed) setTimeout(onComplete, 2000);
        }
      } else {
        const res = await sendCheckinMessage(userId, text);
        if (res.success) {
          const summary = parseCheckinSummary(res.data);
          setMessages((m) => [...m, { role: "assistant", text: res.data.reply, summary }]);
        }
      }
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "Ошибка. Попробуй ещё раз." }]);
    }
    setLoading(false);
  }

  return (
    <div className="chat">
      <div className="chat-header">
        {mode === "onboarding" ? (
          <>
            <h2>Знакомство</h2>
            <p className="chat-subtitle">Расскажи о себе — система начнёт строить твою модель</p>
          </>
        ) : (
          <>
            <h2>Check-in</h2>
            <p className="chat-subtitle">Ежедневная точка ясности. Что сегодня на поверхности?</p>
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
                  {m.summary.improved.length > 0 && (
                    <div className="summary-section summary-up">
                      <span className="summary-label">Обновлено</span>
                      {m.summary.improved.map((t, j) => <span key={j} className="summary-item">{t}</span>)}
                    </div>
                  )}
                  {m.summary.declined.length > 0 && (
                    <div className="summary-section summary-down">
                      <span className="summary-label">Требует внимания</span>
                      {m.summary.declined.map((t, j) => <span key={j} className="summary-item">{t}</span>)}
                    </div>
                  )}
                  {m.summary.newScore != null && (
                    <div className="summary-score">
                      Life Score: <strong>{m.summary.newScore}</strong>
                      {m.summary.scoreDelta != null && m.summary.scoreDelta !== 0 && (
                        <span style={{ color: m.summary.scoreDelta > 0 ? "#22c55e" : "#ef4444", marginLeft: 8 }}>
                          {m.summary.scoreDelta > 0 ? "+" : ""}{m.summary.scoreDelta}
                        </span>
                      )}
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
          placeholder={mode === "checkin" ? "Как ты сегодня?" : "Напиши..."}
          disabled={loading}
        />
        <button onClick={send} disabled={loading || !input.trim()}>&#x2191;</button>
      </div>
    </div>
  );
}
