import { useState, useEffect } from "react";
import { getScenarios, sendPredictionQuery } from "./api";
import { buildPathVM, type PathVM } from "./mappers/scenarios";

interface PredictionSource {
  title: string;
  url: string;
  domain: string;
}

interface PredictionResult {
  questionType: string;
  restatedQuestion: string;
  summary: string;
  influencers: { type: string; name: string; detail: string }[];
  externalInsights: string;
  scenarios: { label: string; title: string; description: string }[];
  dependsOn: string;
  nextStep: string;
  sources: PredictionSource[];
}

const TYPE_LABELS: Record<string, string> = {
  decision: "Решение",
  trajectory: "Траектория",
  change_impact: "Эффект изменения",
  relationship: "Отношения",
  pattern_risk: "Паттерн / риск",
};

export default function PredictionView({ userId }: { userId: string }) {
  const [vm, setVm] = useState<PathVM | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Query state
  const [question, setQuestion] = useState("");
  const [queryLoading, setQueryLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await getScenarios(userId);
        if (res.success && res.data.scenarios?.length) {
          setVm(buildPathVM(res.data));
        }
      } catch {}
      setLoading(false);
    }
    load();
  }, [userId]);

  async function handleAsk() {
    const q = question.trim();
    if (!q || queryLoading) return;
    setQueryLoading(true);
    setResult(null);
    try {
      const res = await sendPredictionQuery(userId, q);
      if (res.success && res.data) {
        setResult({
          questionType: res.data.question_type || "",
          restatedQuestion: res.data.restated_question || "",
          summary: res.data.summary || "",
          influencers: (res.data.influencers || []).map((i: any) => ({
            type: i.type || "", name: i.name || "", detail: i.detail || "",
          })),
          externalInsights: res.data.external_insights || "",
          scenarios: (res.data.scenarios || []).map((s: any) => ({
            label: s.label || "", title: s.title || "", description: s.description || "",
          })),
          dependsOn: res.data.depends_on || "",
          nextStep: res.data.next_step || "",
          sources: (res.data.sources || []).map((s: any) => ({
            title: s.title || "", url: s.url || "", domain: s.domain || "",
          })),
        });
      }
    } catch {}
    setQueryLoading(false);
  }

  return (
    <div className="path-view">
      <div className="path-header">
        <h2>Prediction</h2>
        <p className="path-subtitle">Задай вопрос о своём будущем, выборе или траектории</p>
      </div>

      {/* ── Query Input ── */}
      <div className="pq-input-wrap">
        <input
          className="pq-input"
          type="text"
          placeholder="Что будет, если я...?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleAsk(); }}
          disabled={queryLoading}
        />
        <button className="pq-btn" onClick={handleAsk} disabled={queryLoading || !question.trim()}>
          {queryLoading ? "Думаю..." : "Спросить"}
        </button>
      </div>

      {/* ── Query Result ── */}
      {result && (
        <div className="pq-result">
          {/* Type badge */}
          <div className="pq-type-badge">{TYPE_LABELS[result.questionType] || result.questionType}</div>

          {/* Restated question */}
          {result.restatedQuestion && (
            <div className="pq-section pq-restated">
              <p className="pq-restated-text">"{result.restatedQuestion}"</p>
            </div>
          )}

          {/* Summary */}
          <div className="pq-section">
            <h3 className="pq-section-title">Краткий вывод</h3>
            <p className="pq-text">{result.summary}</p>
          </div>

          {/* Influencers */}
          {result.influencers.length > 0 && (
            <div className="pq-section">
              <h3 className="pq-section-title">Что влияет на прогноз</h3>
              <div className="pq-influencers">
                {result.influencers.map((inf, i) => (
                  <div key={i} className={`pq-influencer pq-inf-${inf.type}`}>
                    <span className="pq-inf-type">{inf.type}</span>
                    <span className="pq-inf-name">{inf.name}</span>
                    {inf.detail && <span className="pq-inf-detail">{inf.detail}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* External insights */}
          {result.externalInsights && (
            <div className="pq-section">
              <h3 className="pq-section-title">Что говорят источники</h3>
              <p className="pq-text">{result.externalInsights}</p>
            </div>
          )}

          {/* Scenarios */}
          {result.scenarios.length > 0 && (
            <div className="pq-section">
              <h3 className="pq-section-title">Сценарии</h3>
              {result.scenarios.map((s, i) => (
                <div key={i} className={`pq-scenario pq-scenario-${s.label}`}>
                  <div className="pq-scenario-label">
                    {s.label === "most_likely" ? "Наиболее вероятный" : "Альтернативный"}
                  </div>
                  <div className="pq-scenario-title">{s.title}</div>
                  <p className="pq-text">{s.description}</p>
                </div>
              ))}
            </div>
          )}

          {/* Depends on */}
          {result.dependsOn && (
            <div className="pq-section">
              <h3 className="pq-section-title">От чего зависит исход</h3>
              <p className="pq-text">{result.dependsOn}</p>
            </div>
          )}

          {/* Next step */}
          {result.nextStep && (
            <div className="pq-section pq-next-step">
              <h3 className="pq-section-title">Следующий шаг</h3>
              <p className="pq-next-step-text">{result.nextStep}</p>
            </div>
          )}

          {/* Sources */}
          {result.sources.length > 0 && (
            <div className="pq-section pq-sources">
              <h3 className="pq-section-title">На что опирался разбор</h3>
              <div className="pq-sources-list">
                {result.sources.map((s, i) => (
                  <a key={i} className="pq-source" href={s.url} target="_blank" rel="noopener noreferrer">
                    <span className="pq-source-domain">{s.domain}</span>
                    <span className="pq-source-title">{s.title}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Old auto-generated scenarios (secondary) ── */}
      {vm && (
        <>
          <div className="pq-divider">
            <span>Автоматические маршруты</span>
          </div>
          <div className="path-scenarios">
            {vm.scenarios.map((s) => (
              <div key={s.type} className={`path-card ${s.isMain ? "path-card-main" : ""}`} style={{ borderLeftColor: s.accent }}>
                <div className="path-card-head">
                  <div>
                    <span className="path-card-type" style={{ color: s.accent }}>{s.label}</span>
                    <div className="path-card-question">{s.question}</div>
                  </div>
                  <span className="path-card-prob" style={{ color: s.accent }}>{s.probability}%</span>
                </div>
                {s.title && <div className="path-card-title">{s.title}</div>}
                {s.narrative && <p className="path-card-narrative">{s.narrative}</p>}
                <div className="path-card-meta">
                  {s.horizonLabel && <div className="path-card-horizon"><span className="path-meta-label">Горизонт:</span> {s.horizonLabel}</div>}
                  <div className="path-card-score">
                    <span className="path-score-from">{s.scoreFrom}</span>
                    <span className="path-score-arrow">&#x2192;</span>
                    <span className="path-score-to">{s.scoreTo}</span>
                    <span className="path-score-delta" style={{ color: s.scoreDelta >= 0 ? "#22c55e" : "#ef4444" }}>
                      ({s.scoreDelta >= 0 ? "+" : ""}{s.scoreDelta})
                    </span>
                  </div>
                  {s.risk && <div className="path-card-risk"><span className="path-meta-label">Риск:</span> {s.risk}</div>}
                  {s.firstStep && <div className="path-card-step"><span className="path-meta-label">Первый шаг:</span> {s.firstStep}</div>}
                </div>
              </div>
            ))}
          </div>

          {(vm.leverage || vm.warning) && (
            <div className="path-insights">
              {vm.leverage && (
                <div className="path-insight-card path-insight-leverage">
                  <div className="path-insight-label">Главная точка влияния</div>
                  <p>{vm.leverage}</p>
                </div>
              )}
              {vm.warning && (
                <div className="path-insight-card path-insight-warning">
                  <div className="path-insight-label">На что обратить внимание</div>
                  <p>{vm.warning}</p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {loading && <div className="path-loading"><div className="spinner" /></div>}

      {!loading && !vm && !result && (
        <p className="empty-state" style={{ marginTop: 24 }}>
          Задай вопрос выше — или сделай несколько чекинов, чтобы появились автоматические маршруты.
        </p>
      )}
    </div>
  );
}
