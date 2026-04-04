import { useState } from "react";
import {
  sendWorkspaceQuery,
  type WorkspaceResult,
  type ScenarioReport,
  type ContextCompleteness,
  type ScenarioComparison,
  type LeverageFactor,
} from "./api";

const TYPE_LABELS: Record<string, string> = {
  decision: "Решение",
  trajectory: "Траектория",
  change_impact: "Эффект изменения",
  relationship: "Отношения",
  pattern_risk: "Паттерн / риск",
};

const CONFIDENCE_LABELS: Record<string, string> = {
  low: "Низкая",
  medium: "Средняя",
  high: "Высокая",
};

const CONFIDENCE_COLORS: Record<string, string> = {
  low: "#ef4444",
  medium: "#f59e0b",
  high: "#22c55e",
};

const WEIGHT_LABELS: Record<string, string> = {
  high: "Сильное",
  medium: "Среднее",
  low: "Слабое",
};

export default function PredictionView({ userId }: { userId: string }) {
  const [question, setQuestion] = useState("");
  const [variants, setVariants] = useState<string[]>([""]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkspaceResult | null>(null);

  function addVariant() {
    setVariants((v) => [...v, ""]);
  }

  function removeVariant(index: number) {
    setVariants((v) => v.filter((_, i) => i !== index));
  }

  function updateVariant(index: number, value: string) {
    setVariants((v) => v.map((item, i) => (i === index ? value : item)));
  }

  async function handleAnalyze() {
    const q = question.trim();
    if (!q || loading) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await sendWorkspaceQuery(userId, q, variants);
      if (res.success && res.data) {
        setResult(res.data as WorkspaceResult);
      }
    } catch {
      /* ignore */
    }
    setLoading(false);
  }

  return (
    <div className="ws-view">
      {/* Header */}
      <div className="ws-header">
        <h2>Decision Workspace</h2>
        <p className="ws-subtitle">
          Смоделируй варианты решения и сравни последствия
        </p>
      </div>

      {/* Question Input */}
      <div className="ws-section">
        <label className="ws-label">Твой вопрос</label>
        <input
          className="ws-input"
          type="text"
          placeholder="Что будет, если я...?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleAnalyze();
          }}
          disabled={loading}
        />
      </div>

      {/* Scenario Variants Editor */}
      <div className="ws-section">
        <label className="ws-label">Варианты сценариев</label>
        <p className="ws-hint">
          Добавь варианты для сравнения. Если оставить пустым — система
          предложит свои.
        </p>
        <div className="ws-variants">
          {variants.map((v, i) => (
            <div key={i} className="ws-variant-row">
              <span className="ws-variant-num">{i + 1}</span>
              <input
                className="ws-variant-input"
                type="text"
                placeholder={`Вариант ${i + 1}, напр. "уволиться в июне"`}
                value={v}
                onChange={(e) => updateVariant(i, e.target.value)}
                disabled={loading}
              />
              {variants.length > 1 && (
                <button
                  className="ws-variant-remove"
                  onClick={() => removeVariant(i)}
                  disabled={loading}
                  title="Удалить"
                >
                  &times;
                </button>
              )}
            </div>
          ))}
          <button
            className="ws-variant-add"
            onClick={addVariant}
            disabled={loading}
          >
            + Добавить вариант
          </button>
        </div>
      </div>

      {/* Run button */}
      <button
        className="ws-run-btn"
        onClick={handleAnalyze}
        disabled={loading || !question.trim()}
      >
        {loading ? "Анализирую сценарии..." : "Запустить анализ"}
      </button>

      {/* Loading */}
      {loading && (
        <div className="ws-loading">
          <div className="spinner" />
          <p>Строю сценарии и сравниваю варианты...</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="ws-results">
          {/* Type + restated question */}
          <div className="ws-result-header">
            <span className="ws-type-badge">
              {TYPE_LABELS[result.question_type] || result.question_type}
            </span>
            {result.restated_question && (
              <div className="ws-restated">"{result.restated_question}"</div>
            )}
          </div>

          {/* Context Completeness */}
          <ContextCompletenessBlock data={result.context_completeness} />

          {/* Scenario Reports */}
          {result.reports.length > 0 && (
            <div className="ws-block">
              <h3 className="ws-block-title">Сценарии</h3>
              <div className="ws-reports">
                {result.reports.map((r, i) => (
                  <ReportCard key={i} report={r} />
                ))}
              </div>
            </div>
          )}

          {/* Comparison */}
          {result.comparison && result.reports.length > 1 && (
            <ComparisonBlock data={result.comparison} />
          )}

          {/* External Insights */}
          {result.external_insights && (
            <div className="ws-block">
              <h3 className="ws-block-title">Что говорят источники</h3>
              <p className="ws-text">{result.external_insights}</p>
            </div>
          )}

          {/* Sources */}
          {result.sources?.length > 0 && (
            <div className="ws-block">
              <h3 className="ws-block-title">Источники</h3>
              <div className="ws-sources">
                {result.sources.map((s, i) => (
                  <a
                    key={i}
                    className="ws-source"
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <span className="ws-source-domain">{s.domain}</span>
                    <span className="ws-source-title">{s.title}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Sub-components ── */

function ContextCompletenessBlock({ data }: { data: ContextCompleteness }) {
  if (!data) return null;
  const color = CONFIDENCE_COLORS[data.score] || CONFIDENCE_COLORS.low;

  return (
    <div className="ws-block ws-context-block">
      <h3 className="ws-block-title">
        Полнота контекста
        <span className="ws-confidence-badge" style={{ color, borderColor: color }}>
          {CONFIDENCE_LABELS[data.score] || data.score}
        </span>
      </h3>

      {data.known_factors?.length > 0 && (
        <div className="ws-context-known">
          <span className="ws-mini-label">Известно:</span>
          <div className="ws-tag-list">
            {data.known_factors.map((f, i) => (
              <span key={i} className="ws-tag ws-tag-known">{f}</span>
            ))}
          </div>
        </div>
      )}

      {data.missing?.length > 0 && (
        <div className="ws-context-missing">
          <span className="ws-mini-label">Чего не хватает:</span>
          <div className="ws-missing-list">
            {data.missing.map((m, i) => (
              <div key={i} className="ws-missing-item">
                <div className="ws-missing-what">{m.what}</div>
                <div className="ws-missing-why">{m.why_important}</div>
                {m.sphere_hint && (
                  <span className="ws-missing-sphere">{m.sphere_hint}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ReportCard({ report }: { report: ScenarioReport }) {
  const confColor = CONFIDENCE_COLORS[report.confidence] || CONFIDENCE_COLORS.low;

  return (
    <div className="ws-report-card">
      <div className="ws-report-head">
        <div className="ws-report-label">{report.variant_label}</div>
        <span
          className="ws-confidence-badge"
          style={{ color: confColor, borderColor: confColor }}
        >
          {CONFIDENCE_LABELS[report.confidence] || report.confidence}
        </span>
      </div>

      {/* Most likely outcome */}
      <div className="ws-report-section">
        <span className="ws-mini-label">Наиболее вероятный исход</span>
        <p className="ws-text">{report.most_likely_outcome}</p>
      </div>

      {/* Alternative */}
      {report.alternative_outcome && (
        <div className="ws-report-section">
          <span className="ws-mini-label">Альтернативный исход</span>
          <p className="ws-text ws-text-muted">{report.alternative_outcome}</p>
        </div>
      )}

      {/* Risks */}
      {report.main_risks?.length > 0 && (
        <div className="ws-report-section">
          <span className="ws-mini-label">Основные риски</span>
          <ul className="ws-risk-list">
            {report.main_risks.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Leverage factors */}
      {report.leverage_factors?.length > 0 && (
        <div className="ws-report-section">
          <span className="ws-mini-label">Что сильнее всего меняет исход</span>
          <div className="ws-leverage-list">
            {report.leverage_factors.map((lf, i) => (
              <LeverageFactorTag key={i} data={lf} />
            ))}
          </div>
        </div>
      )}

      {/* Affected spheres */}
      {report.affected_spheres?.length > 0 && (
        <div className="ws-report-section">
          <span className="ws-mini-label">Затронутые сферы</span>
          <div className="ws-tag-list">
            {report.affected_spheres.map((s, i) => (
              <span key={i} className="ws-tag">{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Next step */}
      {report.next_step && (
        <div className="ws-report-next">
          <span className="ws-mini-label">Следующий шаг</span>
          <p className="ws-next-text">{report.next_step}</p>
        </div>
      )}
    </div>
  );
}

function LeverageFactorTag({ data }: { data: LeverageFactor }) {
  const weightColor =
    data.weight === "high" ? "#ef4444" : data.weight === "medium" ? "#f59e0b" : "#71717a";
  return (
    <div className="ws-leverage-item">
      <span className="ws-leverage-factor">{data.factor}</span>
      <span className="ws-leverage-dir">{data.direction}</span>
      <span className="ws-leverage-weight" style={{ color: weightColor }}>
        {WEIGHT_LABELS[data.weight] || data.weight}
      </span>
    </div>
  );
}

function ComparisonBlock({ data }: { data: ScenarioComparison }) {
  return (
    <div className="ws-block ws-comparison-block">
      <h3 className="ws-block-title">Сравнение сценариев</h3>

      {data.summary && <p className="ws-text">{data.summary}</p>}

      {data.key_tradeoffs?.length > 0 && (
        <div className="ws-comp-section">
          <span className="ws-mini-label">Ключевые trade-offs</span>
          <ul className="ws-tradeoff-list">
            {data.key_tradeoffs.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="ws-comp-grid">
        {data.safest_variant && (
          <div className="ws-comp-cell">
            <span className="ws-mini-label">Безопаснее всего</span>
            <span className="ws-comp-value ws-comp-safe">{data.safest_variant}</span>
          </div>
        )}
        {data.highest_upside_variant && (
          <div className="ws-comp-cell">
            <span className="ws-mini-label">Максимальный потенциал</span>
            <span className="ws-comp-value ws-comp-upside">{data.highest_upside_variant}</span>
          </div>
        )}
        {data.most_sensitive_factor && (
          <div className="ws-comp-cell ws-comp-cell-full">
            <span className="ws-mini-label">Самый чувствительный фактор</span>
            <span className="ws-comp-value ws-comp-factor">{data.most_sensitive_factor}</span>
          </div>
        )}
      </div>
    </div>
  );
}
