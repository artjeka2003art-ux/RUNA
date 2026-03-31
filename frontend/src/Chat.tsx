import { useState, useRef, useEffect } from "react";
import {
  startOnboarding,
  sendOnboardingMessage,
  sendCheckinMessage,
} from "./api";

interface Message {
  role: "user" | "assistant";
  text: string;
}

interface ChatProps {
  userId: string;
  onOnboardingComplete: () => void;
  mode: "onboarding" | "checkin";
}

export default function Chat({ userId, onOnboardingComplete, mode }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Start onboarding automatically
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

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);

    try {
      if (mode === "onboarding") {
        const res = await sendOnboardingMessage(userId, sessionId, text);
        if (res.success) {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", text: res.data.reply },
          ]);
          if (res.data.completed) {
            setTimeout(() => onOnboardingComplete(), 2000);
          }
        }
      } else {
        const res = await sendCheckinMessage(userId, text);
        if (res.success) {
          // Build reply with graph update info
          let reply = res.data.reply;
          const updates = res.data.graph_updates;
          if (updates && updates.total > 0) {
            reply += "\n\n---\n";
            reply += `Граф обновлён: ${updates.total} изменений`;
            if (updates.details) {
              for (const d of updates.details) {
                reply += `\n• ${d}`;
              }
            }
          }
          const score = res.data.life_score;
          if (score) {
            reply += `\n\nLife Score: ${score.total}`;
          }
          setMessages((prev) => [
            ...prev,
            { role: "assistant", text: reply },
          ]);
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Ошибка соединения. Попробуй ещё раз." },
      ]);
    }
    setLoading(false);
  }

  return (
    <div className="chat">
      <div className="chat-header">
        <h2>{mode === "onboarding" ? "Знакомство с Runa" : "Ежедневный чекин"}</h2>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.role === "assistant" && <span className="avatar">R</span>}
            <p>{msg.text}</p>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <span className="avatar">R</span>
            <p className="typing">Runa думает...</p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Напиши что-нибудь..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          →
        </button>
      </div>
    </div>
  );
}
