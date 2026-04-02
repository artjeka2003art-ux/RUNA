import { useState, useEffect } from "react";
import type { RevealData } from "./App";

interface RevealProps {
  data: RevealData;
  onContinue: () => void;
}

export default function Reveal({ data, onContinue }: RevealProps) {
  const [visible, setVisible] = useState(false);
  const [sphereIndex, setSphereIndex] = useState(-1);

  useEffect(() => {
    // Staggered reveal animation
    const t1 = setTimeout(() => setVisible(true), 300);
    const timers = data.spheres.map((_, i) =>
      setTimeout(() => setSphereIndex(i), 800 + i * 400)
    );
    return () => {
      clearTimeout(t1);
      timers.forEach(clearTimeout);
    };
  }, [data.spheres]);

  const count = data.spheres.length;
  const angleStep = (2 * Math.PI) / count;
  const radius = Math.min(140, 100 + count * 5);

  return (
    <div className={`reveal ${visible ? "reveal-visible" : ""}`}>
      <div className="reveal-content">
        <h1 className="reveal-title">Вот как Runa увидела твою жизнь</h1>
        <p className="reveal-subtitle">
          Из нашего разговора система построила {count} сфер — это уникальная карта именно твоей жизни.
          Её можно уточнять дальше.
        </p>

        <div className="reveal-constellation">
          {/* Center point */}
          <div className="reveal-center">
            <span className="reveal-center-score">{Math.round(data.lifeScore)}</span>
            <span className="reveal-center-label">Life Score</span>
          </div>

          {data.spheres.map((s, i) => {
            const angle = angleStep * i - Math.PI / 2;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            const shown = i <= sphereIndex;

            return (
              <div
                key={s.id}
                className={`reveal-sphere ${shown ? "reveal-sphere-visible" : ""}`}
                style={{
                  transform: `translate(${x}px, ${y}px)`,
                }}
              >
                <div className="reveal-sphere-dot" />
                <span className="reveal-sphere-name">{s.name}</span>
                {s.score != null && (
                  <span className="reveal-sphere-score">{Math.round(s.score)}</span>
                )}
              </div>
            );
          })}
        </div>

        <button
          className="reveal-cta"
          onClick={onContinue}
          style={{ opacity: sphereIndex >= count - 1 ? 1 : 0 }}
        >
          Открыть карту жизни
        </button>
      </div>
    </div>
  );
}
