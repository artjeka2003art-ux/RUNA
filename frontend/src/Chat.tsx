import { useState, useRef, useEffect } from "react";
import { startOnboarding, sendOnboardingMessage, sendCheckinMessage } from "./api";

interface Msg {
  role: "user" | "assistant";
  text: string;
}

interface ChatProps {
  userId: string;
  mode: "onboarding" | "checkin";
  onComplete: () => void;
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
          let reply = res.data.reply;
          const upd = res.data.graph_updates;
          if (upd?.total > 0) {
            reply += `\n\n—\nГраф: ${upd.total} изм.`;
            for (const d of (upd.details || []).slice(0, 3)) reply += `\n· ${d}`;
          }
          const score = res.data.life_score;
          if (score) reply += `\n\nLife Score: ${score.total}`;
          setMessages((m) => [...m, { role: "assistant", text: reply }]);
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
        <h2>{mode === "onboarding" ? "Знакомство" : "Чекин"}</h2>
      </div>

      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.role === "assistant" && <span className="msg-avatar">R</span>}
            <div className="msg-bubble">{m.text}</div>
          </div>
        ))}
        {loading && (
          <div className="msg assistant">
            <span className="msg-avatar">R</span>
            <div className="msg-bubble msg-typing">···</div>
          </div>
        )}
        <div ref={bottom} />
      </div>

      <div className="chat-input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Напиши..."
          disabled={loading}
        />
        <button onClick={send} disabled={loading || !input.trim()}>↑</button>
      </div>
    </div>
  );
}
