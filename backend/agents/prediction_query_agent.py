"""Query-based prediction agent.

Takes a user question, classifies it, gathers personal context + external
knowledge, and returns a structured prediction response.
"""

import asyncio
import json
import re
from pathlib import Path

import httpx

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
    def __init__(self, ai_client, graph_client: Neo4jClient):
        self.ai = ai_client
        self.graph = graph_client
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
        personal_context = await self._gather_context(user_id, sphere_id, question)
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
    ) -> str:
        parts: list[str] = []

        try:
            q, p = graph_queries.get_spheres_with_ids(user_id)
            rows = await self.graph.execute_query(q, p)
            if rows:
                parts.append(f"Сферы жизни: {', '.join(r['name'] for r in rows)}")
        except Exception:
            pass

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
                pass

        for label, cypher_label in [("Блокеры", "Blocker"), ("Паттерны", "Pattern")]:
            try:
                q = f"""
                MATCH (n:{cypher_label} {{user_id: $uid}})-[r]->(s:Sphere {{user_id: $uid}})
                RETURN n.name AS name, s.name AS sphere, r.weight AS weight
                ORDER BY r.weight DESC LIMIT 5
                """
                rows = await self.graph.execute_query(q, {"uid": user_id})
                if rows:
                    parts.append(f"\n{label}:")
                    for r in rows:
                        parts.append(f"  - {r['name']} → {r['sphere']} (вес {r.get('weight',0):.2f})")
            except Exception:
                pass

        for ntype in ["Goal", "Value"]:
            try:
                q = f"""
                MATCH (n:{ntype} {{user_id: $uid}})-[r]->(s:Sphere {{user_id: $uid}})
                RETURN n.name AS name, s.name AS sphere, r.weight AS weight
                ORDER BY r.weight DESC LIMIT 3
                """
                rows = await self.graph.execute_query(q, {"uid": user_id})
                if rows:
                    parts.append(f"\n{ntype}s:")
                    for r in rows:
                        parts.append(f"  - {r['name']} → {r['sphere']} (вес {r.get('weight',0):.2f})")
            except Exception:
                pass

        try:
            q, p = graph_queries.get_recent_checkins(user_id, limit=3)
            rows = await self.graph.execute_query(q, p)
            if rows:
                parts.append("\nПоследние чекины:")
                for r in rows:
                    parts.append(f"  - {(r.get('summary','') or '')[:120]}")
        except Exception:
            pass

        try:
            q, p = graph_queries.get_recent_action_feedback(user_id, limit=3)
            rows = await self.graph.execute_query(q, p)
            if rows:
                parts.append("\nНедавние действия:")
                for r in rows:
                    parts.append(f"  - [{r.get('status','')}] {(r.get('one_move','') or '')[:80]}")
        except Exception:
            pass

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

        return "\n".join(parts) if parts else "Контекст пока минимален."

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
        personal_context = await self._gather_context(user_id, sphere_id, question)
        external_context, sources = await self._search_external(question, question_type)

        # Auto-generate variants if user didn't provide them
        if not variants:
            variants = await self._generate_variants(question, question_type)

        result = await self._synthesize_workspace(
            question, question_type, personal_context, external_context, variants,
        )

        result["question"] = question
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

        try:
            resp = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
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
                "context_completeness": {"score": "low", "known_factors": [], "missing": []},
                "reports": [],
                "comparison": None,
                "external_insights": "",
            }

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
