import { useState, useEffect } from "react";
import type { RevealData } from "./App";

interface RevealProps {
  data: RevealData;
  onContinue: () => void;
  onGoToDecisions?: () => void;
}

export default function Reveal({ data, onContinue, onGoToDecisions }: RevealProps) {
  const [visible, setVisible] = useState(false);
  const [sphereIndex, setSphereIndex] = useState(-1);

  useEffect(() => {
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
  const allRevealed = sphereIndex >= count - 1;

  const hasTensions = data.activeTensions && data.activeTensions.length > 0;
  const firstTension = hasTensions ? data.activeTensions![0] : null;

  return (
    <div className={`reveal ${visible ? "reveal-visible" : ""}`}>
      <div className="reveal-content">
        <h1 className="reveal-title">Вот как Runa увидела твою жизнь</h1>
        <p className="reveal-subtitle">
          Из нашего разговора система построила {count} сфер — это первая карта твоей жизни.
          Её можно уточнять и дополнять.
        </p>

        <div className="reveal-constellation">
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

        {firstTension && allRevealed && (
          <div className="reveal-tension">
            <p className="reveal-tension-text">
              Главная развилка: <strong>{firstTension.name}</strong>
            </p>
            {firstTension.description && (
              <p className="reveal-tension-desc">{firstTension.description}</p>
            )}
          </div>
        )}

        <div className="reveal-actions" style={{ opacity: allRevealed ? 1 : 0 }}>
          {hasTensions && onGoToDecisions ? (
            <>
              <button className="reveal-cta" onClick={onGoToDecisions}>
                Разобрать первое решение
              </button>
              <button className="reveal-cta-secondary" onClick={onContinue}>
                Сначала посмотреть карту
              </button>
            </>
          ) : (
            <button className="reveal-cta" onClick={onContinue}>
              Открыть карту жизни
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
