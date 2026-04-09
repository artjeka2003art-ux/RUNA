"""Question mode classifier: maps user questions to QuestionMode.

Uses keyword heuristics with LLM fallback for ambiguous cases.
"""

from __future__ import annotations

import logging
import re

from .models import QuestionMode

logger = logging.getLogger(__name__)

# ── Keyword-based classification ─────────────────────────────────────

_MODE_KEYWORDS: dict[QuestionMode, list[str]] = {
    QuestionMode.investment: [
        "инвест", "акци", "облигац", "портфел", "биткоин", "крипт",
        "купить", "продать", "вложить", "вложен", "рынок", "актив",
        "дивиденд", "etf", "фонд", "трейд", "s&p", "nasdaq",
        "доходност", "bitcoin", "crypto", "stock", "invest",
        "золот", "недвижимост как инвест", "пассивный доход",
    ],
    QuestionMode.career: [
        "уволюсь", "уволиться", "увольнен", "работа", "работу",
        "должност", "компани", "оффер", "offer", "коллег",
        "начальник", "зарплат", "карьер", "повышен", "рабочий",
        "рабочую", "рабочее", "собеседован", "резюме", "найм",
        "удалёнк", "удаленк", "фриланс", "менять работу",
    ],
    QuestionMode.health_activity: [
        "здоровь", "спорт", "тренировк", "бег", "бокс", "зал",
        "фитнес", "йог", "плаван", "режим сна", "сон", "диет",
        "питани", "вес", "похуд", "медицин", "врач", "операци",
        "больниц", "травм", "восстановлен", "recovery",
    ],
    QuestionMode.education: [
        "магистратур", "учёб", "учеб", "универ", "экзамен",
        "обучен", "диплом", "курс", "школ", "mba", "phd",
        "аспирантур", "стажировк", "сертификац", "повышение квалификац",
    ],
    QuestionMode.startup: [
        "стартап", "запуск", "свое дело", "своё дело", "бизнес",
        "предпринимател", "основать", "co-found", "кофаунд",
        "mvp", "product market fit", "инвестор", "раунд",
        "bootstrap", "монетизац",
    ],
    QuestionMode.relationship: [
        "разведусь", "развод", "партнёр", "партнер", "отношени",
        "брак", "жена", "муж", "свадьб", "расстаться",
        "ссор", "измен", "доверие", "близост", "любовь",
    ],
    QuestionMode.relocation: [
        "перееду", "переезд", "релокац", "эмиграц", "иммиграц",
        "другой город", "другую страну", "жить за границ",
        "виз", "вид на жительств",
    ],
}


def _normalize(s: str) -> str:
    return s.lower().replace("ё", "е").strip()


def classify_question_mode(question: str) -> QuestionMode:
    """Classify question into QuestionMode using keyword matching.

    Returns the mode with the highest keyword match count.
    Falls back to general_decision if no strong match.
    """
    q = _normalize(question)
    scores: dict[QuestionMode, int] = {}

    for mode, keywords in _MODE_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in q)
        if hits > 0:
            scores[mode] = hits

    if not scores:
        return QuestionMode.general_decision

    best_mode = max(scores, key=scores.get)  # type: ignore[arg-type]
    best_score = scores[best_mode]

    # Require at least 1 hit to avoid noise
    if best_score < 1:
        return QuestionMode.general_decision

    return best_mode


# ── LLM-based classification (for ambiguous cases) ──────────────────

_CLASSIFY_MODE_PROMPT = """Определи тип жизненного вопроса пользователя. Верни ТОЛЬКО одно слово из списка:
investment, career, health_activity, education, startup, relationship, relocation, general_decision

Описание типов:
- investment: инвестиции, покупка активов, финансовые рынки, крипта
- career: работа, увольнение, карьера, повышение, смена работы
- health_activity: здоровье, спорт, тренировки, режим, медицина
- education: обучение, университет, курсы, магистратура, сертификация
- startup: запуск бизнеса, стартап, предпринимательство
- relationship: отношения, семья, развод, партнёр
- relocation: переезд, эмиграция, смена города/страны
- general_decision: всё остальное, что не попадает ни в одну категорию

Вопрос: {question}

Тип:"""


async def classify_question_mode_llm(
    question: str,
    ai_client,
    model: str,
) -> QuestionMode:
    """LLM-based classification with keyword fallback.

    Uses keywords first. If ambiguous (multiple modes with similar scores),
    defers to LLM.
    """
    # Try keywords first
    q = _normalize(question)
    scores: dict[QuestionMode, int] = {}
    for mode, keywords in _MODE_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in q)
        if hits > 0:
            scores[mode] = hits

    if scores:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        # Clear winner — use it
        if len(sorted_scores) == 1 or sorted_scores[0][1] >= sorted_scores[1][1] * 2:
            return sorted_scores[0][0]

    # Ambiguous or no keywords — use LLM
    try:
        resp = await ai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": _CLASSIFY_MODE_PROMPT.format(question=question)}],
            max_tokens=20,
            temperature=0,
        )
        raw = resp.choices[0].message.content.strip().lower()
        for mode in QuestionMode:
            if mode.value in raw:
                return mode
    except Exception:
        logger.warning("LLM mode classification failed, using keyword fallback", exc_info=True)

    # Final fallback
    if scores:
        return max(scores, key=scores.get)  # type: ignore[arg-type]
    return QuestionMode.general_decision
