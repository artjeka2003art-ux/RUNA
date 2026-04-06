"""Query-based prediction agent.

Takes a user question, classifies it, gathers personal context + external
knowledge, and returns a structured prediction response.
"""

import asyncio
import json
import logging
import re
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

from backend.constants import AI_MODEL
from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries

_FETCH_TIMEOUT = 6.0
_MAX_TEXT_PER_SOURCE = 3000
_STRIP_TAGS = {
    "script", "style", "nav", "footer", "header", "aside", "form",
    "noscript", "iframe", "svg", "button", "figure", "figcaption",
}
# Class/id patterns that indicate non-content blocks
_BOILERPLATE_PATTERNS = re.compile(
    r"cookie|consent|privacy|newsletter|subscribe|signup|sign-up|"
    r"share|social|sidebar|widget|advert|banner|popup|modal|"
    r"related-post|comment|disqus",
    re.IGNORECASE,
)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "prediction_query_prompt.txt"
_WORKSPACE_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "workspace_synthesis_prompt.txt"

# ── Sphere relevance scoring ────────────────────────────────────────

_SPHERE_SYNONYMS: dict[str, list[str]] = {
    "финанс": ["деньги", "бюджет", "доход", "зарплата", "накопления", "подушка"],
    "карьер": ["работа", "профессия", "должность", "рост", "повышение", "компания", "офис", "увольн"],
    "здоровь": ["спорт", "режим", "сон", "тело", "медицин", "врач", "болезн"],
    "отношени": ["партнёр", "партнер", "семья", "любовь", "брак", "близкие", "друзья", "социальн"],
    "образован": ["учёба", "учеба", "магистратура", "курс", "обучени", "навык"],
    "проект": ["стартап", "бизнес", "запуск", "предприниматель"],
    "эмоцион": ["психолог", "терапи", "ментальн", "выгоран", "стресс", "тревог"],
    "семь": ["дети", "ребёнок", "ребенок", "родители", "мама", "папа"],
}

_MAX_RELEVANT_SPHERES = 4


def _normalize(s: str) -> str:
    return s.lower().replace("ё", "е").strip()


def _tokenize(s: str) -> list[str]:
    return [t for t in re.split(r"[\s,.\-—/]+", _normalize(s)) if len(t) > 1]


def _sphere_relevance(sphere_name: str, sphere_desc: str, question: str, variants: list[str]) -> float:
    """Score sphere relevance to question+variants. Returns 0.0-1.0."""
    query_text = _normalize(question + " " + " ".join(variants))
    s_name = _normalize(sphere_name)
    s_desc = _normalize(sphere_desc)

    # Direct mention of sphere name in query
    if s_name in query_text:
        return 1.0

    # Token overlap
    q_tokens = _tokenize(query_text)
    s_tokens = _tokenize(sphere_name + " " + sphere_desc)
    if not q_tokens:
        return 0.1

    overlap = 0
    for qt in q_tokens:
        for st in s_tokens:
            if st in qt or qt in st:
                overlap += 1
                break

    token_score = overlap / max(len(q_tokens), 1)

    # Synonym boost
    synonym_score = 0.0
    for root, aliases in _SPHERE_SYNONYMS.items():
        all_terms = [root] + aliases
        query_hit = any(t in query_text for t in all_terms)
        sphere_hit = any((t in s_name or t in s_desc) for t in all_terms)
        if query_hit and sphere_hit:
            synonym_score = 0.6
            break

    return min(1.0, max(token_score * 0.8, synonym_score))


def _select_relevant_spheres(
    spheres: list[dict], question: str, variants: list[str],
) -> list[dict]:
    """Return top relevant spheres sorted by score. Always returns at least 1 if any exist."""
    if not spheres:
        return []
    scored = []
    for s in spheres:
        score = _sphere_relevance(s["name"], s.get("description", ""), question, variants)
        scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)

    # Take spheres with score > 0.15, but always at least top 1, max _MAX_RELEVANT_SPHERES
    relevant = [s for sc, s in scored if sc > 0.15][:_MAX_RELEVANT_SPHERES]
    if not relevant and scored:
        relevant = [scored[0][1]]
    return relevant


# ── Prediction quality guardrails ───────────────────────────────────

_GENERIC_BLACKLIST = [
    "важно учитывать",
    "стоит обратить внимание",
    "нужно хорошо подумать",
    "всё зависит от многих факторов",
    "может быть полезно",
    "следует тщательно взвесить",
    "это сложный вопрос",
    "нельзя дать точный ответ",
    "необходимо рассмотреть все стороны",
    "нужно учитывать все факторы",
    "подумайте о своих чувствах",
    "найдите баланс",
    "позаботьтесь о себе",
    "поговорите с близкими",
    "взвесьте все за и против",
    "это индивидуальный выбор",
    "только вы можете решить",
    "у каждого варианта есть плюсы и минусы",
    "оба варианта имеют свои преимущества",
]

_REQUIRED_REPORT_FIELDS = [
    "most_likely_outcome",
    "primary_bottleneck",
    "dominant_downside",
    "non_obvious_insight",
    "condition_that_changes_prediction",
    "decision_signal",
]

_REQUIRED_COMPARISON_FIELDS = ["summary", "hidden_trap", "ranking_variable"]

_MIN_FIELD_LENGTH = 15  # fields shorter than this are considered empty/weak


def _check_generic_phrases(text: str) -> list[str]:
    """Find blacklisted generic phrases in text."""
    lower = text.lower()
    return [phrase for phrase in _GENERIC_BLACKLIST if phrase in lower]


def validate_workspace_quality(result: dict) -> tuple[str, list[str]]:
    """Validate workspace prediction quality.

    Returns (quality_score, quality_flags).
    quality_score: 'high' | 'medium' | 'low'
    quality_flags: list of issues found
    """
    flags: list[str] = []

    # Serialize all text for generic check
    full_text = json.dumps(result, ensure_ascii=False)
    generic_hits = _check_generic_phrases(full_text)
    if generic_hits:
        flags.append(f"generic_phrases:{len(generic_hits)}")

    # Check each report
    reports = result.get("reports", [])
    for i, report in enumerate(reports):
        label = report.get("variant_label", f"scenario_{i}")
        for field in _REQUIRED_REPORT_FIELDS:
            val = (report.get(field) or "").strip()
            if len(val) < _MIN_FIELD_LENGTH:
                flags.append(f"weak_field:{label}.{field}")

        # Check decision_signal is not generic
        signal = (report.get("decision_signal") or "").lower()
        if signal and any(p in signal for p in ["важно", "стоит", "подумайте", "учитывайте"]):
            flags.append(f"generic_signal:{label}")

    # Check comparison (if multiple reports)
    comparison = result.get("comparison")
    if len(reports) > 1 and comparison:
        for field in _REQUIRED_COMPARISON_FIELDS:
            val = (comparison.get(field) or "").strip()
            if len(val) < _MIN_FIELD_LENGTH:
                flags.append(f"weak_comparison:{field}")

        # Check comparison summary is not diplomatic filler
        summary = (comparison.get("summary") or "").lower()
        if summary and any(p in summary for p in [
            "оба варианта имеют",
            "у каждого есть",
            "плюсы и минусы",
            "зависит от предпочтений",
        ]):
            flags.append("diplomatic_comparison")

    # Score
    if len(flags) == 0:
        return "high", flags
    elif len(flags) <= 2:
        return "medium", flags
    else:
        return "low", flags


# ── Evidence-backed grounding v2 ───────────────────────────────────

# Semantic synonym groups: bidirectional soft matching
_SEMANTIC_GROUPS: list[list[str]] = [
    ["it", "айти", "технологич", "software", "разработк", "программ", "developer", "инженер"],
    ["финанс", "деньги", "бюджет", "зарплат", "доход", "подушк", "runway", "cash", "накоплен", "сбережен"],
    ["карьер", "работ", "должност", "позиц", "компани", "увольн", "найм", "оффер", "job", "career"],
    ["здоровь", "спорт", "режим", "сон", "выгоран", "burnout", "стресс", "нагрузк", "усталост"],
    ["отношен", "партнер", "семь", "близк", "поддержк", "support", "окружен"],
    ["образован", "учеб", "магистратур", "курс", "обучен", "навык", "диплом"],
    ["проект", "стартап", "бизнес", "запуск", "предпринимател", "свое дело"],
    ["senior", "сеньор", "ведущ", "старш", "lead", "principal"],
    ["junior", "джуниор", "начинающ", "стажер", "intern"],
    ["менеджер", "управлен", "руководител", "тимлид", "manager", "lead"],
]


def _semantic_match(text_a: str, text_b: str) -> bool:
    """Check if two texts share a semantic group (beyond lexical overlap)."""
    a_norm = _normalize(text_a)
    b_norm = _normalize(text_b)
    for group in _SEMANTIC_GROUPS:
        a_hit = any(term in a_norm for term in group)
        b_hit = any(term in b_norm for term in group)
        if a_hit and b_hit:
            return True
    return False


class EvidenceUnit:
    """A single piece of user context evidence."""
    __slots__ = ("source_type", "source_name", "text", "tokens")

    def __init__(self, source_type: str, source_name: str, text: str):
        self.source_type = source_type  # sphere_fact | known_factor | document_fact | sphere_chat
        self.source_name = source_name
        self.text = text
        self.tokens = set(_tokenize(text))

    def matches(self, output_text: str) -> bool:
        """Check if this evidence is reflected in output (lexical + semantic)."""
        out_norm = _normalize(output_text)
        # Lexical: ≥40% of evidence tokens found in output
        if self.tokens:
            hits = sum(1 for t in self.tokens if t in out_norm)
            if hits / len(self.tokens) >= 0.4:
                return True
        # Semantic: evidence and output share a semantic group
        if _semantic_match(self.text, output_text):
            return True
        return False


def build_evidence_pack(
    known_factors: list[str],
    sphere_names: list[str],
    doc_snippets: list[dict],  # [{filename, sphere_name, snippet}]
) -> list[EvidenceUnit]:
    """Build structured evidence pack from available context."""
    evidence: list[EvidenceUnit] = []
    for f in known_factors:
        if len(f.strip()) > 3:
            evidence.append(EvidenceUnit("known_factor", "context", f))
    for s in sphere_names:
        evidence.append(EvidenceUnit("sphere_fact", s, s))
    for d in doc_snippets:
        snippet = d.get("snippet", "")
        if len(snippet) > 20:
            evidence.append(EvidenceUnit("document_fact", d.get("filename", "doc"), snippet[:300]))
    return evidence


def validate_workspace_grounding(
    result: dict,
    evidence: list[EvidenceUnit],
) -> dict:
    """Evidence-backed grounding validation v2.

    Returns dict with:
      grounding_ok: bool
      grounding_score: float (0.0 - 1.0)
      components: {factor_support, sphere_support, document_support}
      flags: list[str]
      evidence_used: list[str]  — evidence texts that matched
      evidence_missed: list[str] — evidence texts that didn't match
    """
    if not evidence:
        return {"grounding_ok": True, "grounding_score": 1.0, "components": {},
                "flags": [], "evidence_used": [], "evidence_missed": []}

    # Collect key output text
    key_text = ""
    for report in result.get("reports", []):
        for field in ("most_likely_outcome", "primary_bottleneck", "decision_signal",
                      "non_obvious_insight", "dominant_downside", "condition_that_changes_prediction"):
            key_text += " " + (report.get(field) or "")
    comparison = result.get("comparison")
    if comparison:
        key_text += " " + (comparison.get("summary") or "")
        key_text += " " + (comparison.get("hidden_trap") or "")

    # Score each evidence unit
    used: list[str] = []
    missed: list[str] = []
    by_type: dict[str, list[bool]] = {}

    for ev in evidence:
        matched = ev.matches(key_text)
        if matched:
            used.append(ev.text)
        else:
            missed.append(ev.text)
        by_type.setdefault(ev.source_type, []).append(matched)

    # Compute per-type support rates
    components: dict[str, float] = {}
    for stype, matches in by_type.items():
        components[stype] = sum(matches) / len(matches) if matches else 0.0

    # Overall grounding score: weighted average
    total_matched = len(used)
    total = len(evidence)
    grounding_score = total_matched / total if total > 0 else 1.0

    # Flags
    flags: list[str] = []
    if grounding_score < 0.15:
        flags.append(f"detached_from_context:{grounding_score:.2f}")
    elif grounding_score < 0.3:
        flags.append(f"weak_grounding:{grounding_score:.2f}")

    if components.get("sphere_fact", 1.0) == 0.0 and len(by_type.get("sphere_fact", [])) > 0:
        flags.append("no_sphere_reference")

    if components.get("document_fact", 1.0) == 0.0 and len(by_type.get("document_fact", [])) > 0:
        flags.append("documents_ignored")

    grounding_ok = len(flags) == 0

    return {
        "grounding_ok": grounding_ok,
        "grounding_score": round(grounding_score, 2),
        "components": {k: round(v, 2) for k, v in components.items()},
        "flags": flags,
        "evidence_used": used[:10],
        "evidence_missed": missed[:10],
    }


# ── Claim-level support mapping v1 ─────────────────────────────────

# Fields ranked by decision-criticality (highest first)
_DECISIVE_FIELDS = ["most_likely_outcome", "primary_bottleneck", "decision_signal"]
_SECONDARY_FIELDS = ["dominant_downside", "condition_that_changes_prediction", "non_obvious_insight"]


class ClaimMapping:
    """A single claim extracted from a scenario report with its support status."""
    __slots__ = ("field", "variant_label", "text", "is_decisive",
                 "supporting_evidence", "support_types", "support_strength")

    def __init__(self, field: str, variant_label: str, text: str, is_decisive: bool):
        self.field = field
        self.variant_label = variant_label
        self.text = text
        self.is_decisive = is_decisive
        self.supporting_evidence: list[str] = []  # evidence texts that match
        self.support_types: set[str] = set()       # source types that match
        self.support_strength: str = "none"        # none | weak | moderate | strong

    @property
    def is_unsupported(self) -> bool:
        return self.support_strength == "none"

    @property
    def is_weak(self) -> bool:
        return self.support_strength in ("none", "weak")

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "variant": self.variant_label,
            "claim": self.text[:120],
            "decisive": self.is_decisive,
            "support": self.support_strength,
            "support_types": sorted(self.support_types),
            "evidence_count": len(self.supporting_evidence),
        }


def extract_claims(result: dict) -> list[ClaimMapping]:
    """Extract key claims from all scenario reports."""
    claims: list[ClaimMapping] = []
    for report in result.get("reports", []):
        label = report.get("variant_label", "?")
        for field in _DECISIVE_FIELDS:
            text = (report.get(field) or "").strip()
            if len(text) >= _MIN_FIELD_LENGTH:
                claims.append(ClaimMapping(field, label, text, is_decisive=True))
        for field in _SECONDARY_FIELDS:
            text = (report.get(field) or "").strip()
            if len(text) >= _MIN_FIELD_LENGTH:
                claims.append(ClaimMapping(field, label, text, is_decisive=False))
    return claims


def map_claims_to_evidence(claims: list[ClaimMapping], evidence: list[EvidenceUnit]) -> None:
    """Match each claim against evidence pack. Mutates claims in-place."""
    for claim in claims:
        for ev in evidence:
            if ev.matches(claim.text):
                claim.supporting_evidence.append(ev.text[:80])
                claim.support_types.add(ev.source_type)

        # Determine support strength
        n = len(claim.supporting_evidence)
        has_doc = "document_fact" in claim.support_types
        if n == 0:
            claim.support_strength = "none"
        elif n == 1 and not has_doc:
            claim.support_strength = "weak"
        elif n <= 2:
            claim.support_strength = "moderate"
        else:
            claim.support_strength = "strong"


def validate_claim_support(claims: list[ClaimMapping]) -> dict:
    """Analyze claim support quality. Returns structured summary."""
    total = len(claims)
    if total == 0:
        return {"ok": True, "flags": [], "summary": {}}

    decisive = [c for c in claims if c.is_decisive]
    unsupported_decisive = [c for c in decisive if c.is_unsupported]
    weak_decisive = [c for c in decisive if c.is_weak]
    supported = [c for c in claims if not c.is_unsupported]
    doc_supported = [c for c in claims if "document_fact" in c.support_types]

    flags: list[str] = []
    if unsupported_decisive:
        names = [f"{c.variant_label}.{c.field}" for c in unsupported_decisive]
        flags.append(f"unsupported_decisive:{','.join(names[:3])}")
    if len(weak_decisive) > len(decisive) / 2 and len(decisive) > 0:
        flags.append("majority_decisive_weak")

    return {
        "ok": len(unsupported_decisive) == 0,
        "flags": flags,
        "summary": {
            "total_claims": total,
            "supported": len(supported),
            "unsupported_decisive": len(unsupported_decisive),
            "weak_decisive": len(weak_decisive),
            "doc_supported": len(doc_supported),
            "support_ratio": round(len(supported) / total, 2) if total > 0 else 0.0,
        },
        "claims": [c.to_dict() for c in claims],
    }


def build_claim_correction_packet(
    claims: list[ClaimMapping], evidence: list[EvidenceUnit],
) -> str:
    """Build targeted correction instructions from claim analysis."""
    lines: list[str] = []

    # Group problem claims by severity
    unsupported_decisive = [c for c in claims if c.is_decisive and c.is_unsupported]
    weak_decisive = [c for c in claims if c.is_decisive and c.support_strength == "weak"]
    unsupported_secondary = [c for c in claims if not c.is_decisive and c.is_unsupported]

    if unsupported_decisive:
        lines.append("### КРИТИЧНО — Неподтверждённые ключевые выводы (ИСПРАВИТЬ ОБЯЗАТЕЛЬНО):")
        for c in unsupported_decisive:
            lines.append(f"  - [{c.variant_label}].{c.field}: \"{c.text[:100]}\"")
            lines.append(f"    Действие: переформулируй опираясь на evidence, ИЛИ ослабь формулировку, ИЛИ явно укажи зависимость от недостающих данных")

    if weak_decisive:
        lines.append("### Слабо подтверждённые ключевые выводы (желательно усилить):")
        for c in weak_decisive:
            lines.append(f"  - [{c.variant_label}].{c.field}: \"{c.text[:100]}\"")
            lines.append(f"    Действие: усиль опору через evidence или сделай формулировку менее абсолютной")

    if unsupported_secondary:
        lines.append("### Неподтверждённые вторичные выводы (можно ослабить):")
        for c in unsupported_secondary[:3]:  # max 3
            lines.append(f"  - [{c.variant_label}].{c.field}: \"{c.text[:80]}\"")

    # Show relevant evidence that should be used
    if evidence:
        ev_texts = [ev.text[:80] for ev in evidence[:8]]
        lines.append("\n### Доступный evidence для опоры:")
        for e in ev_texts:
            lines.append(f"  • {e}")

    return "\n".join(lines) if lines else ""


# ── Confidence Calibration v1 ──────────────────────────────────────

# Evidence type weights for calibration
_EVIDENCE_WEIGHTS: dict[str, float] = {
    "document_fact": 1.5,
    "known_factor": 1.0,
    "sphere_fact": 0.5,
    "sphere_chat": 0.7,
    "memory_fact": 0.8,
}


def calibrate_confidence(
    report: dict,
    claim_result: dict,
    grounding: dict,
    correction: dict | None,
    known_factors: list[str],
    missing_count: int,
    evidence: list["EvidenceUnit"],
) -> dict:
    """Rule-based confidence calibration for a single scenario report.

    Returns {level, reason, limiters, suggestions, inputs}.
    """
    # Gather inputs
    summary = claim_result.get("summary", {})
    support_ratio = summary.get("support_ratio", 0.0)
    unsupported_decisive = summary.get("unsupported_decisive", 0)
    weak_decisive = summary.get("weak_decisive", 0)
    doc_supported = summary.get("doc_supported", 0)
    total_claims = summary.get("total_claims", 0)
    grounding_score = grounding.get("grounding_score", 0.0)
    n_known = len(known_factors)
    still_unsup = len((correction or {}).get("still_unsupported", []))
    n_corrected = len((correction or {}).get("corrected", []))
    retry_used = correction is not None

    # Evidence quality: weighted score
    ev_quality = 0.0
    if evidence:
        ev_quality = sum(_EVIDENCE_WEIGHTS.get(ev.source_type, 0.5) for ev in evidence) / len(evidence)

    # Has strong evidence types?
    has_doc_evidence = any(ev.source_type == "document_fact" for ev in evidence)
    has_semantic_only = grounding_score > 0.3 and not any(
        ev.source_type in ("document_fact", "known_factor") for ev in evidence if ev.matches(
            " ".join((report.get(f) or "") for f in _DECISIVE_FIELDS)
        )
    )

    # ── Rule engine ──
    level = "high"  # start optimistic, cap down
    limiters: list[str] = []
    suggestions: list[str] = []

    # Hard caps
    if still_unsup > 0:
        level = "low"
        limiters.append(f"{still_unsup} ключевых вывод(а/ов) не подтверждены даже после correction")
        suggestions.append("Добавьте конкретные факты в релевантные сферы")

    if unsupported_decisive > 0 and not retry_used:
        level = "low"
        limiters.append(f"{unsupported_decisive} ключевых вывод(а/ов) без опоры на контекст")

    if grounding_score < 0.15:
        level = "low"
        limiters.append("Прогноз слабо связан с вашими данными")
        suggestions.append("Расскажите больше о ситуации в сферах")

    # Medium caps
    if level != "low":
        if n_known < 3:
            if level == "high":
                level = "medium"
            limiters.append(f"Мало фактов ({n_known}) — прогноз опирается на ограниченные данные")
            suggestions.append("Добавьте больше фактов о вашей ситуации")

        if missing_count > 5:
            if level == "high":
                level = "medium"
            limiters.append(f"Много пробелов в контексте ({missing_count})")

        if support_ratio < 0.4:
            level = "low"
            limiters.append(f"Только {int(support_ratio*100)}% выводов подтверждены контекстом")
        elif support_ratio < 0.6:
            if level == "high":
                level = "medium"
            limiters.append(f"{int(support_ratio*100)}% выводов подтверждены — есть пробелы")

        if weak_decisive > 0 and unsupported_decisive == 0:
            if level == "high":
                level = "medium"
            limiters.append(f"{weak_decisive} ключевых вывод(а/ов) подтверждены слабо")

        if has_semantic_only:
            if level == "high":
                level = "medium"
            limiters.append("Связь с контекстом преимущественно косвенная")

        # Coarse claim granularity cap: if decisive fields are long and treated as single claim
        for f in _DECISIVE_FIELDS:
            val = report.get(f, "")
            if isinstance(val, str) and len(val) > 200 and level == "high":
                level = "medium"
                limiters.append("Составные выводы проверены укрупнённо")
                break

    # Positive signals (can promote from medium to high, never from low)
    if level == "medium":
        promoted = False
        if support_ratio >= 0.7 and n_known >= 5 and unsupported_decisive == 0:
            level = "high"
            promoted = True
        if doc_supported > 0 and support_ratio >= 0.6 and not promoted:
            level = "high"
            promoted = True
        if n_corrected > 0 and still_unsup == 0 and support_ratio >= 0.5 and not promoted:
            level = "high"

    # Document bump: add positive note but don't magically elevate
    if has_doc_evidence and doc_supported > 0:
        if not suggestions:
            pass  # already strong
        limiters_note = f"Документы подтверждают {doc_supported} вывод(а/ов)"
        if limiters_note not in limiters:
            limiters.append(limiters_note)

    # Failed retry penalty
    if retry_used and still_unsup > 0:
        if level == "medium":
            level = "low"
        limiters.append("Targeted correction не смог подтвердить все ключевые выводы")

    # Build reason
    if level == "high":
        reason = "Ключевые выводы подтверждены контекстом"
        if doc_supported > 0:
            reason += " и документами"
        reason += f" ({int(support_ratio*100)}% support)"
    elif level == "medium":
        reason = ". ".join(limiters[:2]) if limiters else "Контекст частичный"
    else:
        reason = ". ".join(limiters[:2]) if limiters else "Недостаточно данных"

    return {
        "level": level,
        "reason": reason,
        "limiters": limiters[:5],
        "suggestions": suggestions[:3],
        "inputs": {
            "support_ratio": round(support_ratio, 2),
            "grounding_score": round(grounding_score, 2),
            "known_factors": n_known,
            "missing_count": missing_count,
            "unsupported_decisive": unsupported_decisive,
            "still_unsupported": still_unsup,
            "doc_supported": doc_supported,
            "ev_quality": round(ev_quality, 2),
        },
    }


_CORRECTION_PROMPT = """Предыдущий ответ содержит проблемы quality. Исправь его.

## Проблемы найденные в ответе:
{issues}

## Контекст пользователя для привязки:
{grounding_context}

{claim_corrections}

## Правила исправления:
1. Убери ВСЕ generic фразы ("важно учитывать", "стоит обратить внимание" и подобные)
2. Каждое пустое или слабое поле заполни КОНКРЕТНЫМ содержанием
3. decision_signal — короткий вердикт ("Сильный при X" / "Слабый без Y"), НЕ совет

### Правила для неподтверждённых claims:
4. Если claim НЕПОДТВЕРЖДЁН и есть релевантный evidence — переформулируй, опираясь на evidence
5. Если claim НЕПОДТВЕРЖДЁН и evidence недостаточен — ОСЛАБЬ формулировку (добавь "при условии", "если", "вероятно")
6. Если claim НЕЛЬЗЯ честно подтвердить — замени на явное указание зависимости: "Зависит от [конкретного факта]" или "Требует уточнения [чего именно]"
7. НЕ повторяй сильные утверждения без опоры. Лучше честно слабый claim, чем fake-confident.
8. ОБЯЗАТЕЛЬНО используй данные из evidence: known factors, сферы, документы.

## Предыдущий ответ (JSON):
{previous_output}

Верни ИСПРАВЛЕННЫЙ JSON. Только валидный JSON, без markdown, без ```:
"""


_QUESTION_TYPES = {
    "decision": "Вопрос о конкретном выборе / решении",
    "trajectory": "Вопрос о текущей траектории / к чему ведёт",
    "change_impact": "Вопрос о последствиях конкретного изменения",
    "relationship": "Вопрос об отношениях / межличностном напряжении",
    "pattern_risk": "Вопрос о повторяющемся паттерне / риске",
}

_CLASSIFY_PROMPT = """Определи тип вопроса пользователя. Верни ТОЛЬКО одно слово из списка:
decision, trajectory, change_impact, relationship, pattern_risk

Вопрос: {question}

Тип:"""


class PredictionQueryAgent:
    def __init__(
        self,
        ai_client,
        graph_client: Neo4jClient,
        session_store=None,
        zep_client=None,
        document_store=None,
    ):
        self.ai = ai_client
        self.graph = graph_client
        self.sessions = session_store
        self.zep = zep_client
        self.docs = document_store
        self._prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
        self._workspace_prompt_template = _WORKSPACE_PROMPT_PATH.read_text(encoding="utf-8")

    # ── Public API ───────────────────────────────────────────────────

    async def answer(
        self,
        user_id: str,
        question: str,
        sphere_id: str | None = None,
    ) -> dict:
        """Full prediction pipeline: classify → context → search → synthesize."""

        question_type = await self._classify_question(question)
        personal_context, _, _, _ = await self._gather_context(user_id, sphere_id, question)
        external_context, sources = await self._search_external(question, question_type)

        result = await self._synthesize(
            question, question_type, personal_context, external_context,
        )

        result["question_type"] = question_type
        result["sources"] = sources
        return result

    # ── Step 1: Classification ───────────────────────────────────────

    async def _classify_question(self, question: str) -> str:
        try:
            resp = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": _CLASSIFY_PROMPT.format(question=question)}],
                max_tokens=20,
                temperature=0,
            )
            raw = resp.choices[0].message.content.strip().lower()
            for t in _QUESTION_TYPES:
                if t in raw:
                    return t
            return "trajectory"
        except Exception:
            return "trajectory"

    # ── Step 2: Personal context retrieval ────────────────────────────

    async def _gather_context(
        self, user_id: str, sphere_id: str | None, question: str,
        variants: list[str] | None = None,
    ) -> str:
        parts: list[str] = []

        # Sphere list with descriptions
        all_spheres: list[dict] = []  # [{id, name, description}]
        try:
            q, p = graph_queries.get_spheres_with_descriptions(user_id)
            rows = await self.graph.execute_query(q, p)
            if rows:
                all_spheres = [{"id": r["id"], "name": r["name"], "description": r.get("description", "")} for r in rows]
        except Exception:
            logger.warning("Failed to fetch spheres for user %s", user_id, exc_info=True)

        # Select only relevant spheres for this question
        relevant_spheres = _select_relevant_spheres(all_spheres, question, variants or [])

        # Ensure focused sphere is always included
        if sphere_id:
            focused_ids = {s["id"] for s in relevant_spheres}
            if sphere_id not in focused_ids:
                focused = next((s for s in all_spheres if s["id"] == sphere_id), None)
                if focused:
                    relevant_spheres.insert(0, focused)

        # Show relevant spheres in detail, others just as names
        if all_spheres:
            relevant_names = {s["name"] for s in relevant_spheres}
            rel_lines = []
            other_names = []
            for s in all_spheres:
                if s["name"] in relevant_names:
                    line = s["name"]
                    if s["description"]:
                        line += f" — {s['description']}"
                    rel_lines.append(line)
                else:
                    other_names.append(s["name"])
            header = "Релевантные сферы для этого вопроса:\n" + "\n".join(f"  - {l}" for l in rel_lines)
            if other_names:
                header += f"\nДругие сферы ({len(other_names)}): {', '.join(other_names)}"
            parts.append(header)

        # Use relevant_spheres for detailed context gathering
        context_spheres = relevant_spheres

        # Focused sphere detail
        if sphere_id:
            try:
                q, p = graph_queries.get_sphere_detail(user_id, sphere_id)
                rows = await self.graph.execute_query(q, p)
                if rows:
                    row = rows[0]
                    parts.append(f"\nФокусная сфера: {row.get('name', '')}")
                    for node in (row.get("related") or []):
                        if node:
                            labels = node.get("labels", [])
                            parts.append(f"  {labels[0] if labels else '?'}: {node.get('name','')} (вес {node.get('weight',0):.2f})")
            except Exception:
                logger.warning("Failed to fetch sphere detail %s", sphere_id, exc_info=True)

        # Graph entities: blockers, patterns, goals, values
        for label, cypher_label in [("Блокеры", "Blocker"), ("Паттерны", "Pattern")]:
            try:
                q = f"""
                MATCH (n:{cypher_label} {{user_id: $uid}})-[r]->(s:Sphere {{user_id: $uid}})
                RETURN n.name AS name, n.description AS desc, s.name AS sphere, r.weight AS weight
                ORDER BY r.weight DESC LIMIT 5
                """
                rows = await self.graph.execute_query(q, {"uid": user_id})
                if rows:
                    parts.append(f"\n{label}:")
                    for r in rows:
                        line = f"  - {r['name']} → {r['sphere']} (вес {r.get('weight',0):.2f})"
                        if r.get("desc"):
                            line += f" — {r['desc'][:80]}"
                        parts.append(line)
            except Exception:
                pass

        for ntype in ["Goal", "Value"]:
            try:
                q = f"""
                MATCH (n:{ntype} {{user_id: $uid}})-[r]->(s:Sphere {{user_id: $uid}})
                RETURN n.name AS name, n.description AS desc, s.name AS sphere, r.weight AS weight
                ORDER BY r.weight DESC LIMIT 3
                """
                rows = await self.graph.execute_query(q, {"uid": user_id})
                if rows:
                    parts.append(f"\n{ntype}s:")
                    for r in rows:
                        line = f"  - {r['name']} → {r['sphere']} (вес {r.get('weight',0):.2f})"
                        if r.get("desc"):
                            line += f" — {r['desc'][:80]}"
                        parts.append(line)
            except Exception:
                pass

        # Recent checkins
        try:
            q, p = graph_queries.get_recent_checkins(user_id, limit=3)
            rows = await self.graph.execute_query(q, p)
            if rows:
                parts.append("\nПоследние чекины:")
                for r in rows:
                    parts.append(f"  - {(r.get('summary','') or '')[:120]}")
        except Exception:
            pass

        # Recent action feedback
        try:
            q, p = graph_queries.get_recent_action_feedback(user_id, limit=3)
            rows = await self.graph.execute_query(q, p)
            if rows:
                parts.append("\nНедавние действия:")
                for r in rows:
                    parts.append(f"  - [{r.get('status','')}] {(r.get('one_move','') or '')[:80]}")
        except Exception:
            pass

        # Recent weight changes
        try:
            q, p = graph_queries.get_recent_weight_changes_detailed(user_id, limit=5)
            rows = await self.graph.execute_query(q, p)
            if rows:
                parts.append("\nНедавние изменения в графе:")
                for r in rows:
                    d = r.get("delta", 0)
                    parts.append(f"  - {r.get('from_name','')} → {r.get('to_name','')}: {'+'if d>0 else ''}{d:.2f}")
        except Exception:
            pass

        # Sphere chat context: compact digests from Redis sessions
        sphere_chat_context = await self._gather_sphere_chat_context(user_id, context_spheres, question)
        if sphere_chat_context:
            parts.append(sphere_chat_context)

        # Zep long-term memory facts (if available)
        zep_context = await self._gather_zep_context(user_id, context_spheres)
        if zep_context:
            parts.append(zep_context)

        # Document context from uploaded files
        doc_context, doc_names, doc_snippets = await self._gather_document_context(
            user_id, context_spheres, question, variants or [],
        )
        if doc_context:
            parts.append(doc_context)

        context = "\n".join(parts) if parts else "Контекст пока минимален."
        return context, [s["name"] for s in context_spheres], doc_names, doc_snippets

    async def _gather_context_with_spheres(
        self, user_id: str, sphere_id: str | None, question: str,
        variants: list[str] | None = None,
    ) -> tuple[str, list[str], list[str], list[dict]]:
        """Wrapper that returns (context_text, used_sphere_names, used_doc_names, doc_snippets)."""
        return await self._gather_context(user_id, sphere_id, question, variants)

    async def _gather_sphere_chat_context(
        self, user_id: str, sphere_ids: list[dict], question: str,
    ) -> str:
        """Build compact sphere digests from Redis chat sessions.

        Instead of raw messages, produces a structured digest per sphere:
        name, description, key user facts (deduplicated, truncated).
        """
        if not self.sessions or not sphere_ids:
            return ""

        digests: list[str] = []

        for s in sphere_ids:
            session_key = f"sphere-{user_id}-{s['id']}"
            try:
                history = await self.sessions.get_session(session_key)
                if not history:
                    continue
                # Extract user messages only
                user_msgs = [m["content"] for m in history if m.get("role") == "user"]
                if not user_msgs:
                    continue

                # Build compact digest
                digest_lines = [f"  【{s['name']}】"]
                if s.get("description"):
                    digest_lines.append(f"    Описание: {s['description'][:120]}")

                # Deduplicate, score by question relevance, pick top 4
                q_tokens = _tokenize(question)
                seen = set()
                scored_facts: list[tuple[float, str]] = []
                for msg in reversed(user_msgs):
                    short = msg[:200].strip()
                    norm = _normalize(short)
                    if len(norm) < 15 or norm in seen:
                        continue
                    seen.add(norm)
                    # Score: token overlap with question gives priority
                    overlap = sum(1 for t in q_tokens if t in norm) if q_tokens else 0
                    score = overlap / max(len(q_tokens), 1) + 0.01  # tiny base so all are orderable
                    scored_facts.append((score, short))

                # Sort by relevance, take top 4
                scored_facts.sort(key=lambda x: x[0], reverse=True)
                facts = [text for _, text in scored_facts[:4]]

                if facts:
                    digest_lines.append("    Факты от пользователя:")
                    for f in reversed(facts):
                        digest_lines.append(f"      • {f[:150]}")

                digests.append("\n".join(digest_lines))
            except Exception:
                continue

        if not digests:
            return ""
        return "\nДайджест релевантных сфер:\n" + "\n".join(digests)

    async def _gather_zep_context(self, user_id: str, sphere_ids: list[dict]) -> str:
        """Pull Zep long-term facts for relevant spheres (if Zep is connected)."""
        if not self.zep or not sphere_ids:
            return ""

        facts: list[str] = []
        for s in sphere_ids[:5]:  # limit to 5 spheres
            thread_id = f"sphere-{user_id}-{s['id']}"
            try:
                ctx = await self.zep.get_user_context(user_id, thread_id)
                if ctx and len(ctx.strip()) > 10:
                    facts.append(f"  «{s['name']}»: {ctx[:200]}")
            except Exception:
                continue

        if not facts:
            return ""
        return "\nДолгосрочная память по сферам:\n" + "\n".join(facts)

    async def _gather_document_context(
        self,
        user_id: str,
        context_spheres: list[dict],
        question: str,
        variants: list[str],
    ) -> tuple[str, list[str], list[dict]]:
        """Pull extracted text from sphere documents.

        Returns (context_str, doc_filenames, doc_snippets_for_evidence).
        doc_snippets: [{filename, sphere_name, snippet}] for grounding checks.
        """
        if not self.docs or not context_spheres:
            return "", [], []

        q_tokens = _tokenize(question + " " + " ".join(variants))
        doc_parts: list[str] = []
        doc_names: list[str] = []
        doc_snippets: list[dict] = []

        for s in context_spheres:
            try:
                docs = await self.docs.get_documents(user_id, s["id"])
                if not docs:
                    continue
                for doc in docs:
                    if doc.get("status") not in ("processed", "limited"):
                        continue
                    text = doc.get("extracted_text", "")
                    if len(text) < 20:
                        continue

                    # Question-aware: score relevance of doc text to question
                    doc_lower = _normalize(text[:2000])
                    relevance = sum(1 for t in q_tokens if t in doc_lower) / max(len(q_tokens), 1)

                    excerpt = text[:800] if relevance > 0.1 else text[:400]
                    status_note = " (частично извлечён)" if doc["status"] == "limited" else ""
                    doc_parts.append(
                        f"  📄 {doc['filename']}{status_note} [{s['name']}]:\n    {excerpt}"
                    )
                    doc_names.append(doc["filename"])
                    # Save snippet for evidence grounding (first 300 chars of content)
                    doc_snippets.append({
                        "filename": doc["filename"],
                        "sphere_name": s["name"],
                        "snippet": text[:300],
                    })
            except Exception:
                logger.warning("Failed to fetch docs for sphere %s", s["id"], exc_info=True)
                continue

        if not doc_parts:
            return "", [], []
        return "\nДокументы пользователя:\n" + "\n".join(doc_parts), doc_names, doc_snippets

    # ── Step 3: External knowledge retrieval ──────────────────────────

    _SEARCH_QUERY_PROMPT = """Сформируй один поисковый запрос на английском для поиска профессиональных статей и исследований.

Вопрос пользователя: {question}
Тип вопроса: {qtype}

Требования к запросу:
- На английском
- Ищи общие закономерности, риски, условия успеха — НЕ прямой ответ
- Ориентируйся на research, expert frameworks, evidence-based материалы
- Одна строка, без кавычек

Запрос:"""

    _REJECT_DOMAINS = {
        "pinterest.com", "facebook.com", "instagram.com", "tiktok.com",
        "twitter.com", "x.com", "reddit.com", "quora.com", "youtube.com",
        "wikihow.com", "buzzfeed.com", "boredpanda.com", "9gag.com",
        "diply.com", "shareably.net", "thoughtcatalog.com",
    }

    _HIGH_TRUST_PATTERNS = [
        ".edu", ".gov", ".ac.", ".org",
        "ncbi.nlm.nih.gov", "pubmed", "scholar.google",
        "apa.org", "who.int", "mayoclinic.org", "nih.gov",
        "harvard.edu", "stanford.edu", "mit.edu",
        "nature.com", "sciencedirect.com", "springer.com",
        "frontiersin.org", "bmc", "plos", "mdpi.com",
    ]

    _MEDIUM_TRUST_PATTERNS = [
        "psychologytoday.com", "verywellmind.com", "hbr.org",
        "bbc.com", "theatlantic.com", "newyorker.com",
        "wired.com", "arstechnica.com", "scientificamerican.com",
        "ted.com", "nytimes.com", "theguardian.com",
        "mckinsey.com", "forbes.com",
    ]

    _CLICKBAIT_TITLE_SIGNALS = [
        "top 10", "top 5", "top 7", "top 15", "top 20",
        "you won't believe", "ultimate guide", "hack your",
        "secrets to", "things you", "signs you",
        "best ways to", "simple tricks",
    ]

    _TYPE_PREFERRED_DOMAINS: dict[str, list[str]] = {
        "decision": ["hbr.org", "mckinsey", "decision", "career", "management"],
        "trajectory": ["research", "longitudinal", "outcomes", "psychology"],
        "change_impact": ["behaviour", "habit", "change", "intervention", "meta-analysis"],
        "relationship": ["psychology", "attachment", "relationship", "counselling", "therapy", "family"],
        "pattern_risk": ["psychology", "behavioural", "addiction", "risk", "clinical", "cognitive"],
    }

    # ── Quality scoring ──────────────────────────────────────────────

    def _score_result(self, result: dict, question_type: str) -> float:
        href = (result.get("href", "") or "").lower()
        title = (result.get("title", "") or "").lower()
        body = (result.get("body", "") or "")
        score = 0.5

        if any(p in href for p in self._HIGH_TRUST_PATTERNS):
            score += 0.3
        elif any(p in href for p in self._MEDIUM_TRUST_PATTERNS):
            score += 0.15

        if any(sig in title for sig in self._CLICKBAIT_TITLE_SIGNALS):
            score -= 0.25

        if len(body) > 200:
            score += 0.1
        elif len(body) < 60:
            score -= 0.15

        preferred = self._TYPE_PREFERRED_DOMAINS.get(question_type, [])
        if any(p in href or p in title for p in preferred):
            score += 0.1

        if any(w in href for w in ["shop", "buy", "product", "pricing", "affiliate"]):
            score -= 0.3

        return max(0.0, min(1.0, score))

    # ── Full-text extraction (improved) ──────────────────────────────

    @staticmethod
    def _extract_main_text(html: str) -> str:
        """Extract clean main text from HTML."""
        try:
            from bs4 import BeautifulSoup, Tag
        except ImportError:
            return ""

        soup = BeautifulSoup(html, "html.parser")

        # Remove junk tags
        for tag in soup.find_all(list(_STRIP_TAGS)):
            tag.decompose()

        # Remove boilerplate blocks by class/id patterns
        for tag in soup.find_all(True):
            attrs = " ".join([
                " ".join(tag.get("class", [])),
                tag.get("id", ""),
            ])
            if attrs and _BOILERPLATE_PATTERNS.search(attrs):
                tag.decompose()

        # Pick best container: prefer <article>, then <main>,
        # then the <div> with most text density, then <body>
        container = soup.find("article") or soup.find("main")
        if not container:
            # Find densest div (most direct text children)
            best_div = None
            best_len = 0
            for div in soup.find_all("div"):
                text = div.get_text(strip=True)
                if len(text) > best_len:
                    best_len = len(text)
                    best_div = div
            container = best_div or soup.find("body")

        if not container:
            return ""

        raw = container.get_text(separator="\n")

        # Clean up — keep lines >= 10 chars (less aggressive than 20)
        lines = []
        for line in raw.splitlines():
            line = line.strip()
            if len(line) < 10:
                continue
            lines.append(line)

        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text[:_MAX_TEXT_PER_SOURCE]

    async def _fetch_page_text(self, url: str) -> str:
        """Download page and extract main text. Returns empty on failure."""
        try:
            async with httpx.AsyncClient(
                timeout=_FETCH_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; RunaBot/1.0)"},
            ) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return ""
                ct = resp.headers.get("content-type", "")
                if "text/html" not in ct:
                    return ""
                return self._extract_main_text(resp.text)
        except Exception:
            return ""

    @staticmethod
    def _domain_from_url(url: str) -> str:
        try:
            return url.split("/")[2]
        except (IndexError, AttributeError):
            return ""

    # ── Search + filter + fetch pipeline ─────────────────────────────

    async def _build_search_query(self, question: str, question_type: str) -> str:
        try:
            resp = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": (
                    self._SEARCH_QUERY_PROMPT
                    .replace("{question}", question)
                    .replace("{qtype}", _QUESTION_TYPES.get(question_type, question_type))
                )}],
                max_tokens=60,
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip().strip('"').strip("'")
        except Exception:
            return question

    async def _search_external(
        self, question: str, question_type: str,
    ) -> tuple[str, list[dict]]:
        """Returns (context_for_synthesis, sources_list_for_response)."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            try:
                from ddgs import DDGS
            except ImportError:
                return "", []

        search_query = await self._build_search_query(question, question_type)

        try:
            raw_results = []
            with DDGS() as ddgs:
                for r in ddgs.text(search_query, max_results=12):
                    raw_results.append(r)
        except Exception:
            return "", []

        if not raw_results:
            return "", []

        # 1. Hard reject junk domains
        candidates = []
        for r in raw_results:
            href = (r.get("href", "") or "").lower()
            domain = self._domain_from_url(href)
            if any(junk in domain for junk in self._REJECT_DOMAINS):
                continue
            candidates.append(r)

        if not candidates:
            return "", []

        # 2. Score + sort
        scored = [(self._score_result(r, question_type), r) for r in candidates]
        scored.sort(key=lambda x: x[0], reverse=True)

        # 3. Top 3 with quality >= 0.4
        top = [(s, r) for s, r in scored if s >= 0.4][:3]

        if not top:
            return (
                "Качественных профессиональных источников по этому вопросу "
                "найти не удалось. Вывод основан на личном контексте пользователя.",
                [],
            )

        # 4. Fetch full text in PARALLEL
        async def _fetch_one(sc: float, r: dict) -> tuple[float, dict, str]:
            href = r.get("href", "")
            full_text = await self._fetch_page_text(href) if href else ""
            if len(full_text) > 500:
                sc = min(1.0, sc + 0.1)
            elif len(full_text) < 100 and full_text:
                sc = max(0.0, sc - 0.1)
            return sc, r, full_text

        enriched = await asyncio.gather(*[_fetch_one(s, r) for s, r in top])

        # 5. Quality label
        avg_score = sum(s for s, _, _ in enriched) / len(enriched)
        if avg_score >= 0.7:
            quality_note = "Найдены содержательные профессиональные материалы."
        elif avg_score >= 0.5:
            quality_note = "Найдены материалы среднего уровня. Выводы вероятностные."
        else:
            quality_note = "Доступные материалы ограничены. Выводы следует воспринимать осторожно."

        # 6. Build context for synthesis + source list for response
        parts = [
            f"Поисковый запрос: \"{search_query}\"",
            f"Качество источников: {quality_note}\n",
        ]
        sources: list[dict] = []

        for i, (sc, r, full_text) in enumerate(enriched, 1):
            title = r.get("title", "")
            href = r.get("href", "")
            domain = self._domain_from_url(href)

            if full_text and len(full_text) > 100:
                content = full_text
                source_type = "полный текст"
            else:
                content = (r.get("body", "") or "")[:300]
                source_type = "snippet"

            parts.append(
                f"{i}. [{sc:.1f}] {title} ({source_type})\n"
                f"   {content}\n"
                f"   Источник: {href}\n"
            )
            sources.append({"title": title, "url": href, "domain": domain})

        return "\n".join(parts), sources

    # ── Public API: Decision Workspace ─────────────────────────────

    _DEFAULT_VARIANTS_PROMPT = """Пользователь задал вопрос о жизненном решении, но не указал конкретные варианты сценариев.

Вопрос: {question}
Тип: {question_type}

Предложи 2-3 конкретных варианта сценария для анализа. Каждый вариант — короткая фраза (3-7 слов).
Верни ТОЛЬКО JSON массив строк, без markdown:
["вариант 1", "вариант 2", "вариант 3"]"""

    async def workspace(
        self,
        user_id: str,
        question: str,
        sphere_id: str | None = None,
        variants: list[str] | None = None,
    ) -> dict:
        """Decision Workspace pipeline: classify → context → search → multi-scenario synthesis."""

        question_type = await self._classify_question(question)

        # Auto-generate variants early so they inform context selection
        if not variants:
            variants = await self._generate_variants(question, question_type)

        personal_context, used_sphere_names, used_doc_names, doc_snippets = await self._gather_context_with_spheres(user_id, sphere_id, question, variants)
        external_context, sources = await self._search_external(question, question_type)

        result = await self._synthesize_workspace(
            question, question_type, personal_context, external_context, variants,
            sphere_names=used_sphere_names, doc_names=used_doc_names,
            doc_snippets=doc_snippets,
        )

        result["question"] = question
        result["context_spheres_used"] = used_sphere_names
        result["documents_used"] = used_doc_names
        result["question_type"] = question_type
        result["variants"] = variants
        result["sources"] = sources
        return result

    async def _generate_variants(self, question: str, question_type: str) -> list[str]:
        """Ask LLM to propose scenario variants when user didn't specify them."""
        try:
            resp = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": (
                    self._DEFAULT_VARIANTS_PROMPT
                    .replace("{question}", question)
                    .replace("{question_type}", _QUESTION_TYPES.get(question_type, question_type))
                )}],
                max_tokens=200,
                temperature=0.3,
            )
            raw = resp.choices[0].message.content.strip()
            start = raw.find("[")
            end = raw.rfind("]")
            if start != -1 and end != -1:
                return json.loads(raw[start:end + 1])
        except Exception:
            pass
        return [question]

    async def _synthesize_workspace(
        self,
        question: str,
        question_type: str,
        personal_context: str,
        external_context: str,
        variants: list[str],
        sphere_names: list[str] | None = None,
        doc_names: list[str] | None = None,
        doc_snippets: list[dict] | None = None,
    ) -> dict:
        variants_text = "\n".join(f"- {v}" for v in variants)
        prompt = (
            self._workspace_prompt_template
            .replace("{question}", question)
            .replace("{question_type}", _QUESTION_TYPES.get(question_type, question_type))
            .replace("{personal_context}", personal_context)
            .replace("{external_context}", external_context or "Внешние источники пока не подключены.")
            .replace("{variants}", variants_text)
        )

        sphere_names = sphere_names or []
        doc_names = doc_names or []
        doc_snippets = doc_snippets or []

        try:
            result = await self._call_workspace_llm(prompt)

            # Build evidence pack from available context
            known_factors = result.get("context_completeness", {}).get("known_factors", [])
            evidence = build_evidence_pack(known_factors, sphere_names, doc_snippets)

            # 1. Quality guardrails (genericness + sharpness)
            quality_score, quality_flags = validate_workspace_quality(result)

            # 2. Grounding guardrails v2 (evidence-backed)
            grounding = validate_workspace_grounding(result, evidence)
            grounding_flags = grounding["flags"]

            # 3. Claim-level support mapping
            claims = extract_claims(result)
            map_claims_to_evidence(claims, evidence)
            claim_result = validate_claim_support(claims)
            claim_flags = claim_result["flags"]

            all_flags = quality_flags + grounding_flags + claim_flags

            # Determine combined score (claim-aware)
            has_unsupported_decisive = any("unsupported_decisive" in f for f in claim_flags)
            if quality_score == "low" or any("detached" in f for f in grounding_flags):
                combined_score = "low"
            elif has_unsupported_decisive:
                combined_score = "low"  # unsupported decisive claim = always low
            elif len(all_flags) <= 2:
                combined_score = quality_score
            else:
                combined_score = "medium" if quality_score == "high" else quality_score

            # 4. Corrective retry if combined is low — now claim-aware
            retry_used = False
            pre_retry_unsupported: list[str] = []
            corrected_claims: list[str] = []
            still_unsupported: list[str] = []

            if combined_score == "low" and all_flags:
                # Capture pre-retry unsupported decisive claims
                pre_retry_unsupported = [
                    f"{c.variant_label}.{c.field}" for c in claims
                    if c.is_decisive and c.is_unsupported
                ]

                logger.info("Claim-aware correction triggered (%d flags, %d unsupported decisive), retrying",
                            len(all_flags), len(pre_retry_unsupported))

                grounding_context = self._build_grounding_reminder(known_factors, sphere_names, doc_names)
                claim_packet = build_claim_correction_packet(claims, evidence)

                corrected = await self._retry_workspace_correction(
                    result, all_flags, grounding_context, claim_packet,
                )
                if corrected:
                    result = corrected
                    retry_used = True
                    new_known = result.get("context_completeness", {}).get("known_factors", [])
                    evidence = build_evidence_pack(new_known, sphere_names, doc_snippets)
                    quality_score, quality_flags = validate_workspace_quality(result)
                    grounding = validate_workspace_grounding(result, evidence)
                    grounding_flags = grounding["flags"]
                    claims = extract_claims(result)
                    map_claims_to_evidence(claims, evidence)
                    claim_result = validate_claim_support(claims)
                    claim_flags = claim_result["flags"]
                    all_flags = quality_flags + grounding_flags + claim_flags
                    has_unsupported_decisive = any("unsupported_decisive" in f for f in claim_flags)

                    # Track which claims were fixed vs still unsupported
                    post_unsupported = {
                        f"{c.variant_label}.{c.field}" for c in claims
                        if c.is_decisive and c.is_unsupported
                    }
                    corrected_claims = [c for c in pre_retry_unsupported if c not in post_unsupported]
                    still_unsupported = [c for c in pre_retry_unsupported if c in post_unsupported]

                    if len(all_flags) == 0:
                        combined_score = "high"
                    elif has_unsupported_decisive:
                        combined_score = "low"
                    elif len(all_flags) <= 2:
                        combined_score = "medium"
                    else:
                        combined_score = "low"

            # 5. Confidence calibration v1
            missing_count = len(result.get("context_completeness", {}).get("missing", []))
            correction_meta = {
                "corrected": corrected_claims,
                "still_unsupported": still_unsupported,
            } if retry_used else None

            for report in result.get("reports", []):
                cal = calibrate_confidence(
                    report, claim_result, grounding, correction_meta,
                    known_factors, missing_count, evidence,
                )
                # Override LLM confidence with calibrated value
                report["confidence"] = cal["level"]
                report["confidence_reason"] = cal["reason"]
                report["_calibration"] = cal

            result["_quality"] = {
                "score": combined_score,
                "flags": all_flags,
                "retry_used": retry_used,
                "genericness_ok": len(quality_flags) == 0,
                "grounding_ok": grounding["grounding_ok"],
                "grounding_score": grounding["grounding_score"],
                "grounding_components": grounding["components"],
                "evidence_used": grounding["evidence_used"],
                "evidence_missed": grounding["evidence_missed"],
                "claim_support": claim_result["summary"],
                "claims": claim_result.get("claims", [])[:8],
                "correction": {
                    "targeted_claims": pre_retry_unsupported,
                    "corrected": corrected_claims,
                    "still_unsupported": still_unsupported,
                } if retry_used else None,
            }
            return result
        except Exception:
            logger.warning("Workspace synthesis failed", exc_info=True)
            return {
                "restated_question": question,
                "context_completeness": {"score": "low", "known_factors": [], "missing": []},
                "reports": [],
                "comparison": None,
                "external_insights": "",
                "_quality": {"score": "low", "flags": ["synthesis_failed"], "retry_used": False,
                             "genericness_ok": False, "grounding_ok": False,
                             "grounding_score": 0.0, "grounding_components": {},
                             "evidence_used": [], "evidence_missed": [],
                             "claim_support": {}, "claims": []},
            }

    async def _call_workspace_llm(self, prompt: str) -> dict:
        """Call LLM and parse JSON response."""
        resp = await self.ai.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
        return json.loads(raw)

    @staticmethod
    def _build_grounding_reminder(
        known_factors: list[str], sphere_names: list[str], doc_names: list[str],
    ) -> str:
        """Build compact context reminder for correction prompt."""
        parts = []
        if known_factors:
            parts.append(f"Known factors: {', '.join(known_factors[:10])}")
        if sphere_names:
            parts.append(f"Сферы: {', '.join(sphere_names)}")
        if doc_names:
            parts.append(f"Документы: {', '.join(doc_names)}")
        return "\n".join(parts) if parts else "Контекст минимален."

    async def _retry_workspace_correction(
        self, previous: dict, flags: list[str],
        grounding_context: str = "",
        claim_packet: str = "",
    ) -> dict | None:
        """One corrective retry with claim-aware correction instructions."""
        issues_text = "\n".join(f"- {f}" for f in flags)
        prev_json = json.dumps(previous, ensure_ascii=False, indent=2)

        if len(prev_json) > 8000:
            prev_json = prev_json[:8000] + "\n... (truncated)"

        correction_prompt = (
            _CORRECTION_PROMPT
            .replace("{issues}", issues_text)
            .replace("{previous_output}", prev_json)
            .replace("{grounding_context}", grounding_context or "Контекст минимален.")
            .replace("{claim_corrections}", claim_packet or "")
        )

        try:
            resp = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": correction_prompt}],
                max_tokens=4000,
                temperature=0.3,
            )
            raw = resp.choices[0].message.content.strip()
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                raw = raw[start:end + 1]
            return json.loads(raw)
        except Exception:
            logger.warning("Quality correction retry failed", exc_info=True)
            return None

    # ── Step 4: Synthesis (legacy single-answer) ────────────────────

    async def _synthesize(
        self,
        question: str,
        question_type: str,
        personal_context: str,
        external_context: str,
    ) -> dict:
        prompt = (
            self._prompt_template
            .replace("{question}", question)
            .replace("{question_type}", _QUESTION_TYPES.get(question_type, question_type))
            .replace("{personal_context}", personal_context)
            .replace("{external_context}", external_context or "Внешние источники пока не подключены.")
        )

        try:
            resp = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.4,
            )
            raw = resp.choices[0].message.content.strip()
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                raw = raw[start:end + 1]
            return json.loads(raw)
        except (json.JSONDecodeError, Exception):
            return {
                "restated_question": question,
                "summary": "Не удалось сгенерировать prediction. Попробуй переформулировать вопрос.",
                "influencers": [],
                "external_insights": "",
                "scenarios": [],
                "depends_on": "",
                "next_step": "",
            }
