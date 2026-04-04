from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries
from backend.models.schemas import LifeScore, SphereScore, NextStep, DailyCompass, FocusSphere, ActionTrace


_POSITIVE_TYPES = {"Goal", "Value"}
_NEGATIVE_TYPES = {"Blocker"}
_BASE_SCORE = 50.0
_MAX_SHIFT_PER_NODE = 15.0


def _compute_daily_state(total: float) -> tuple[str, str]:
    """Fallback daily state used by LifeScore (non-compass)."""
    if total >= 75:
        return "Устойчивость", "Система видит устойчивые опоры в нескольких сферах."
    if total >= 60:
        return "Восстановление", "Часть опор уже собирается. Одно верное действие в день — достаточно."
    if total >= 45:
        return "Поиск опоры", "Не хаос, но и не точка силы. Выбери одно направление."
    if total >= 30:
        return "Под давлением", "Давление в нескольких сферах. Но есть направление, где можно начать."
    return "Кризис", "Сейчас тяжело. Найдём один маленький шаг."


def _compute_compass_state(
    total: float,
    delta: float,
    strongest_worsening: dict | None,
    strongest_improvement: dict | None,
    top_blocker_weight: float,
) -> tuple[str, str]:
    """Rich daily state that reads like a human feeling, not a score bucket."""

    # 1. Strong positive momentum overrides score range
    if delta >= 5:
        return "В точке сдвига", (
            "Что-то сдвинулось. Не останавливайся — "
            "сейчас самое время закрепить движение."
        )
    if delta >= 2 and total >= 50:
        return "В движении", (
            "Ты набираешь ход. Не нужно ускоряться — "
            "просто не теряй контакт с тем, что работает."
        )

    # 2. Active resistance — score ok-ish but blocker pressure high
    if top_blocker_weight >= 0.7 and total >= 40:
        return "В сопротивлении", (
            "Внутри идёт борьба. Ты не слаб — "
            "но что-то мешает войти в действие. Важно понять что именно."
        )

    # 3. Negative momentum — things are getting worse
    if delta <= -5:
        return "Под давлением", (
            "Давление растёт. Это не приговор — "
            "но если не сделать один шаг сегодня, завтра будет тяжелее."
        )
    if delta <= -2 and strongest_worsening:
        wname = strongest_worsening.get("to_name", "")
        return "Теряю опору", (
            f'Ты теряешь контакт с тем, что держало. '
            f'Особенно в сфере "{wname}".'
            if wname else
            'Часть опор ослабевает. Нужно вернуть контакт хотя бы с одной.'
        )

    # 4. Slow recovery
    if delta > 0 and total < 50:
        return "В восстановлении", (
            "Медленно, но ты возвращаешься. "
            "Не гони. Одно действие в день — достаточно."
        )

    # 5. Score-based fallback (but with better language)
    if total >= 75:
        return "Устойчивость", (
            "Опоры держат. Твоя задача — не разбрасываться, "
            "а углублять то, что уже работает."
        )
    if total >= 60:
        return "Возвращение в контакт", (
            "Ты на пути. Не всё собрано, но направление есть. "
            "Держи фокус на одной сфере."
        )
    if total >= 45:
        return "Поиск опоры", (
            "Пока нет чёткой точки силы. "
            "Выбери одно направление и начни с малого."
        )
    if total >= 30:
        return "Под давлением", (
            "Несколько сфер давят одновременно. "
            "Не пытайся починить всё — выбери одну."
        )
    return "Кризис", (
        "Сейчас тяжело. Это нормально. "
        "Найдём один маленький шаг, который можно сделать сегодня."
    )


# ── One Move action templates ──────────────────────────────────────

_BLOCKER_ACTIONS: list[tuple[float, str, str]] = [
    # (min_weight, action_template, reason_template)
    # {b} = blocker name, {s} = sphere name, {w} = weight
    (0.7,
     'Запиши одним сообщением: что именно ты избегаешь в "{s}" из-за "{b}".',
     '"{b}" забирает слишком много сил (вес {w:.1f}). Назвать — уже полдела.'),
    (0.5,
     '15 минут черновой работы в "{s}" — без попытки сделать хорошо.',
     '"{b}" мешает начать. Снизь планку до минимума — важнее контакт, чем результат.'),
    (0.0,
     'Верни контакт с "{s}": 10 минут, без цели решить всё.',
     '"{b}" пока не критичен, но растёт. Лучше не ждать.'),
]

_SUPPORT_ACTIONS: list[str] = [
    'Используй то, что уже работает: "{sup}". Сделай один шаг в "{s}", опираясь на это.',
    'У тебя есть "{sup}" — это реальная опора. 15 минут в "{s}", начиная оттуда.',
]

_GENERIC_ACTIONS: list[str] = [
    'Открой сферу "{s}" и напиши одно сообщение о том, что сейчас происходит.',
    'Выдели 10 минут на "{s}" — просто вернуть контакт, без плана.',
]


def _build_next_step(
    weakest: SphereScore | None,
    blockers: list[dict],
    supports: list[dict],
    recent_changes: list[dict],
    last_checkin: str | None,
) -> NextStep:
    if not weakest:
        return NextStep()

    sphere = weakest.sphere
    score = round(weakest.score)

    relevant_blocker = None
    for b in blockers:
        if b.get("sphere") == sphere or not relevant_blocker:
            relevant_blocker = b
            if b.get("sphere") == sphere:
                break

    relevant_support = None
    for s in supports:
        if s.get("sphere") == sphere or not relevant_support:
            relevant_support = s
            if s.get("sphere") == sphere:
                break

    worsening = [c for c in recent_changes if c.get("delta", 0) < -0.05]
    improving = [c for c in recent_changes if c.get("delta", 0) > 0.05]

    if relevant_blocker:
        blocker_name = relevant_blocker["name"]
        weight = relevant_blocker.get("weight", 0.5)
        action = f'Займись блокером "{blocker_name}"'
        if weight >= 0.7:
            action += " — он сильно давит и отнимает больше всего очков."
        else:
            action += " — даже частичное снятие даст сдвиг."
    else:
        action = f'Сделай одно конкретное действие в сфере "{sphere}".'

    why_parts = [f'"{sphere}" на {score} — самая уязвимая сфера']
    if worsening:
        worst = worsening[0]
        why_parts.append(f'связь "{worst.get("from_name", "?")}" ухудшилась за последний чекин')
    elif last_checkin:
        snippet = last_checkin[:60].rstrip()
        if len(last_checkin) > 60:
            snippet += "..."
        why_parts.append(f'в последнем чекине ты говорил: "{snippet}"')
    why = ". ".join(why_parts) + "."

    if relevant_support:
        support_name = relevant_support["name"]
        outcome = f'Опирайся на "{support_name}" — это уже работает в твоём графе.'
    elif improving:
        imp = improving[0]
        outcome = f'Позитивный тренд: "{imp.get("from_name", "?")}" уже растёт. Продолжай.'
    else:
        if relevant_blocker:
            impact = round(relevant_blocker.get("weight", 0.5) * _MAX_SHIFT_PER_NODE, 1)
            outcome = f"Убрав этот блокер, ты поднимешь сферу примерно на {impact} очков."
        else:
            outcome = "Любое осознанное действие здесь сдвинет общий Life Score."

    return NextStep(action=action, why=why, outcome=outcome)


class LifeScoreEngine:
    def __init__(self, graph_client: Neo4jClient):
        self.graph = graph_client

    async def calculate(self, user_id: str) -> LifeScore:
        """Pure read — calculates current score without writing anything to the DB.

        Safe to call from GET endpoints. Does NOT create ScoreHistory or
        update Person.last_total.
        """
        query, params = graph_queries.get_spheres(user_id)
        sphere_rows = await self.graph.execute_query(query, params)

        if not sphere_rows:
            state, reason = _compute_daily_state(_BASE_SCORE)
            return LifeScore(
                user_id=user_id, total=_BASE_SCORE, spheres=[],
                daily_state=state, daily_state_reason=reason,
            )

        sphere_scores = []
        for row in sphere_rows:
            score = await self._calculate_sphere_score(user_id, row["name"])
            sphere_scores.append(score)

        total = round(sum(s.score for s in sphere_scores) / len(sphere_scores), 1)
        state, reason = _compute_daily_state(total)

        # Delta is read-only: compare against last committed snapshot
        score_delta = await self._read_score_delta(user_id, total)

        sorted_spheres = sorted(sphere_scores, key=lambda s: s.score)
        weakest = sorted_spheres[0] if sorted_spheres else None

        blockers, supports = await self._get_blockers_and_supports(user_id)
        recent_changes = await self._get_recent_weight_changes(user_id)
        last_checkin = await self._get_last_checkin(user_id)

        next_step = _build_next_step(weakest, blockers, supports, recent_changes, last_checkin)

        return LifeScore(
            user_id=user_id, total=total, spheres=sphere_scores,
            daily_state=state, daily_state_reason=reason,
            score_delta=round(score_delta, 1), next_step=next_step,
        )

    async def commit_score_snapshot(self, user_id: str, life_score: LifeScore):
        """Write-only — saves a score snapshot after a real state change.

        Call this ONLY after: onboarding complete, check-in, analyst update.
        NEVER call from GET /score.
        """
        total = life_score.total
        try:
            # Update Person.last_total
            q = "MATCH (p:Person {user_id: $uid}) SET p.last_total = $total"
            await self.graph.execute_query(q, {"uid": user_id, "total": total})

            # Create ScoreHistory point
            q2 = """
            CREATE (sh:ScoreHistory {
                user_id: $uid,
                total: $total,
                created_at: datetime()
            })
            """
            await self.graph.execute_query(q2, {"uid": user_id, "total": total})
        except Exception:
            pass

    async def calculate_compass(self, user_id: str) -> DailyCompass:
        """Build Daily Compass — the retention core of Today screen."""

        # ── Gather all data ──────────────────────────────────────────
        life_score = await self.calculate(user_id)
        total = life_score.total
        spheres = life_score.spheres
        score_delta = life_score.score_delta

        blockers, supports = await self._get_blockers_and_supports(user_id)

        q, p = graph_queries.get_recent_weight_changes_detailed(user_id, limit=15)
        changes = await self.graph.execute_query(q, p) or []

        # Separate worsening / improving changes
        worsening = [c for c in changes if c.get("delta", 0) < -0.03]
        improving = [c for c in changes if c.get("delta", 0) > 0.03]

        strongest_worsening = max(worsening, key=lambda c: abs(c["delta"]), default=None)
        strongest_improvement = max(improving, key=lambda c: c["delta"], default=None)

        # Top blocker weight across all spheres
        top_blocker_weight = max((b.get("weight", 0) for b in blockers), default=0.0)

        # ── 0. Load recent action feedback ──────────────────────────
        last_feedback = None
        last_action_trace = None
        try:
            q_fb, p_fb = graph_queries.get_recent_action_feedback(user_id, limit=1)
            fb_rows = await self.graph.execute_query(q_fb, p_fb)
            if fb_rows:
                last_feedback = fb_rows[0]
        except Exception:
            pass

        # ── 1. Daily State (rich, multi-signal) ──────────────────────
        daily_state, daily_state_reason = _compute_compass_state(
            total, score_delta,
            strongest_worsening, strongest_improvement,
            top_blocker_weight,
        )

        # Adjust daily state based on yesterday's action
        if last_feedback:
            fb_status = last_feedback.get("status", "")
            fb_sphere = last_feedback.get("sphere_name", "")
            if fb_status == "done" and score_delta >= 0:
                daily_state_reason = (
                    f'Вчера ты сделал шаг в "{fb_sphere}". '
                    + daily_state_reason
                    if fb_sphere else daily_state_reason
                )
            elif fb_status == "not_done" and fb_sphere:
                # Don't change state but note inertia in reason
                daily_state_reason = (
                    f'Вчерашний шаг в "{fb_sphere}" не случился — напряжение осталось. '
                    + daily_state_reason
                )

        # ── 2. Focus Sphere (composite, not just lowest) ────────────
        focus_sphere = await self._pick_focus_sphere(
            user_id, spheres, blockers, changes,
        )

        # ── 3. Key Shift (human language) ────────────────────────────
        key_shift_title, key_shift_reason = self._build_key_shift(
            changes, strongest_worsening, strongest_improvement,
        )

        # ── 4. One Move (concrete action template) ──────────────────
        one_move, one_move_reason = self._build_one_move(
            focus_sphere, blockers, supports,
        )

        # If yesterday's move was not_done, reinforce urgency
        if last_feedback and last_feedback.get("status") == "not_done":
            fb_sphere = last_feedback.get("sphere_name", "")
            if fb_sphere and focus_sphere and fb_sphere == focus_sphere.name:
                one_move_reason = (
                    f'Вчера этот шаг не случился. Сегодня — второй шанс. '
                    + one_move_reason
                )

        # ── 5. Cost of Ignoring (short, specific) ───────────────────
        cost_of_ignoring = self._build_cost_of_ignoring(
            focus_sphere, blockers, worsening, changes,
        )

        # ── 6. Last Action Trace (UI block) ─────────────────────────
        if last_feedback:
            fb_status = last_feedback.get("status", "")
            fb_sphere = last_feedback.get("sphere_name", "")
            fb_move = last_feedback.get("one_move", "")
            if fb_status == "done":
                trace_msg = (
                    f'Вчера ты сделал шаг в "{fb_sphere}". '
                    f'Система учла это — и это уже влияет на сегодняшний фокус.'
                    if fb_sphere else
                    'Вчера ты сделал шаг. Система учла это в сегодняшнем расчёте.'
                )
            else:
                trace_msg = (
                    f'Вчерашний шаг в "{fb_sphere}" не случился. '
                    f'Это нормально — но напряжение пока осталось.'
                    if fb_sphere else
                    'Вчерашний шаг не случился. Напряжение пока осталось.'
                )
            last_action_trace = ActionTrace(
                status=fb_status,
                message=trace_msg,
                sphere_name=fb_sphere,
            )

        return DailyCompass(
            daily_state=daily_state,
            daily_state_reason=daily_state_reason,
            key_shift_title=key_shift_title,
            key_shift_reason=key_shift_reason,
            focus_sphere=focus_sphere,
            one_move=one_move,
            one_move_reason=one_move_reason,
            cost_of_ignoring=cost_of_ignoring,
            last_action_trace=last_action_trace,
        )

    # ── Compass sub-builders ─────────────────────────────────────────

    async def _pick_focus_sphere(
        self,
        user_id: str,
        spheres: list[SphereScore],
        blockers: list[dict],
        changes: list[dict],
    ) -> FocusSphere | None:
        """Pick the most important sphere right now — not just the weakest."""
        if not spheres:
            return None

        # Build sphere ID map
        q, p = graph_queries.get_spheres_with_scores_data(user_id)
        sphere_rows = await self.graph.execute_query(q, p)
        id_map = {r["name"]: r["id"] for r in (sphere_rows or [])}

        # Composite score: lower = higher priority
        # Factors: raw score (inverted), blocker pressure, recent negative momentum
        blocker_pressure: dict[str, float] = {}
        for b in blockers:
            s = b.get("sphere", "")
            w = b.get("weight", 0)
            blocker_pressure[s] = blocker_pressure.get(s, 0) + w

        negative_momentum: dict[str, float] = {}
        for c in changes:
            if c.get("delta", 0) < 0 and c.get("to_label") == "Sphere":
                s = c.get("to_name", "")
                negative_momentum[s] = negative_momentum.get(s, 0) + abs(c["delta"])

        best = None
        best_priority = -1.0
        for sp in spheres:
            sid = id_map.get(sp.sphere)
            if not sid:
                continue
            # Invert score: 100 - score → low score = high priority
            score_factor = (100.0 - sp.score) / 100.0
            pressure_factor = min(blocker_pressure.get(sp.sphere, 0) / 1.0, 1.0)
            momentum_factor = min(negative_momentum.get(sp.sphere, 0) / 0.5, 1.0)

            priority = score_factor * 0.4 + pressure_factor * 0.35 + momentum_factor * 0.25

            if priority > best_priority:
                best_priority = priority
                best = FocusSphere(id=sid, name=sp.sphere, score=round(sp.score, 1))

        return best

    @staticmethod
    def _build_key_shift(
        changes: list[dict],
        strongest_worsening: dict | None,
        strongest_improvement: dict | None,
    ) -> tuple[str, str]:
        """Human-readable key shift — what changed in your life, not in the graph."""
        if not changes:
            return "", ""

        # Prefer worsening (more actionable), fall back to improvement
        if strongest_worsening and abs(strongest_worsening.get("delta", 0)) >= abs(
            (strongest_improvement or {}).get("delta", 0)
        ):
            c = strongest_worsening
            fn = c.get("from_name", "")
            tn = c.get("to_name", "")
            fl = c.get("from_label", "")

            if fl == "Blocker":
                title = f'"{fn}" усилился'
                reason = (
                    f'Ты снова начал избегать "{tn}" через "{fn}". '
                    f'Это не слабость — но важно заметить.'
                )
            elif fl == "Pattern":
                title = f'Паттерн "{fn}" набирает силу'
                reason = (
                    f'"{fn}" начинает давить на "{tn}". '
                    f'Если не обратить внимание, он закрепится.'
                )
            else:
                title = f'В "{tn}" стало меньше опоры'
                reason = (
                    f'Связь с "{fn}" ослабла. '
                    f'Это бьёт по устойчивости в "{tn}".'
                )
        elif strongest_improvement:
            c = strongest_improvement
            fn = c.get("from_name", "")
            tn = c.get("to_name", "")
            fl = c.get("from_label", "")

            if fl in ("Goal", "Value"):
                title = f'"{fn}" становится реальной опорой'
                reason = f'Ты укрепляешь "{fn}" — и это уже работает для "{tn}".'
            else:
                title = f'Сдвиг в "{tn}"'
                reason = (
                    f'Что-то начало меняться в "{tn}" после последнего разговора. '
                    f'Хороший знак.'
                )
        else:
            return "", ""

        return title, reason

    @staticmethod
    def _build_one_move(
        focus: FocusSphere | None,
        blockers: list[dict],
        supports: list[dict],
    ) -> tuple[str, str]:
        """One concrete, time-bounded action — not advice."""
        if not focus:
            return "", ""

        s = focus.name
        sphere_blockers = [b for b in blockers if b.get("sphere") == s]
        sphere_supports = [sup for sup in supports if sup.get("sphere") == s]

        if sphere_blockers:
            b = sphere_blockers[0]
            bname = b["name"]
            w = b.get("weight", 0.5)
            for min_w, action_tpl, reason_tpl in _BLOCKER_ACTIONS:
                if w >= min_w:
                    return (
                        action_tpl.format(b=bname, s=s, w=w),
                        reason_tpl.format(b=bname, s=s, w=w),
                    )

        if sphere_supports:
            sup = sphere_supports[0]
            return (
                _SUPPORT_ACTIONS[0].format(sup=sup["name"], s=s),
                f'"{sup["name"]}" — реальная точка силы. Начни оттуда.',
            )

        return (
            _GENERIC_ACTIONS[0].format(s=s),
            f'"{s}" на {focus.score} — самая уязвимая. Даже 10 минут контакта сдвинут картину.',
        )

    @staticmethod
    def _build_cost_of_ignoring(
        focus: FocusSphere | None,
        blockers: list[dict],
        worsening: list[dict],
        changes: list[dict],
    ) -> str:
        """Short, specific warning — one sentence."""
        if not focus:
            return ""

        s = focus.name

        # Find strongest blocker in focus sphere
        sphere_blockers = [b for b in blockers if b.get("sphere") == s]
        top_blocker = sphere_blockers[0] if sphere_blockers else None

        # Find other spheres being affected by worsening
        affected = {
            c.get("to_name", "")
            for c in worsening
            if c.get("to_label") == "Sphere" and c.get("to_name") != s
        }

        if top_blocker and top_blocker.get("weight", 0) >= 0.6:
            bname = top_blocker["name"]
            if affected:
                other = next(iter(affected))
                return (
                    f'"{bname}" продолжит расти и потянет за собой "{other}".'
                )
            return (
                f'Ещё несколько дней — и "{bname}" закрепится. '
                f'Вернуть контакт с "{s}" будет тяжелее.'
            )

        if affected:
            other = next(iter(affected))
            return f'Давление из "{s}" уже перетекает в "{other}".'

        return f'Без внимания "{s}" станет точкой, которая тянет вниз всё остальное.'

    # ── Private helpers (all read-only) ──────────────────────────────

    async def _calculate_sphere_score(self, user_id: str, sphere_name: str) -> SphereScore:
        query, params = graph_queries.get_sphere_connections(user_id, sphere_name)
        connections = await self.graph.execute_query(query, params)

        score = _BASE_SCORE
        reasons = []

        for conn in connections:
            node_labels = set(conn.get("node_labels", []))
            node_name = conn.get("node_name", "")
            weight = conn.get("weight", 0.5)
            shift = weight * _MAX_SHIFT_PER_NODE

            if node_labels & _POSITIVE_TYPES:
                score += shift
                reasons.append(f"+{node_name}")
            elif node_labels & _NEGATIVE_TYPES:
                score -= shift
                reasons.append(f"-{node_name}")
            else:
                score += shift * 0.2
                reasons.append(f"~{node_name}")

        score = max(0.0, min(100.0, score))
        reason = ", ".join(reasons[:3]) if reasons else "нет данных"

        return SphereScore(sphere=sphere_name, score=round(score, 1), delta=0.0, reason=reason)

    async def _read_score_delta(self, user_id: str, current_total: float) -> float:
        """Read-only: get delta vs last committed snapshot. Does NOT write."""
        try:
            q = "MATCH (p:Person {user_id: $uid}) RETURN p.last_total AS last_total"
            rows = await self.graph.execute_query(q, {"uid": user_id})
            prev = rows[0]["last_total"] if rows and rows[0].get("last_total") is not None else None
            return (current_total - prev) if prev is not None else 0.0
        except Exception:
            return 0.0

    async def _get_blockers_and_supports(self, user_id: str) -> tuple[list[dict], list[dict]]:
        blockers = []
        supports = []
        try:
            q_b = """
            MATCH (b:Blocker {user_id: $uid})-[r]->(s:Sphere {user_id: $uid})
            RETURN b.name AS name, s.name AS sphere, r.weight AS weight
            ORDER BY r.weight DESC
            """
            rows = await self.graph.execute_query(q_b, {"uid": user_id})
            seen = set()
            for row in (rows or []):
                name = row.get("name", "")
                if name not in seen:
                    seen.add(name)
                    blockers.append({
                        "name": name, "type": "Blocker",
                        "sphere": row.get("sphere", ""),
                        "weight": row.get("weight", 0.5),
                    })

            for node_type in ["Goal", "Value"]:
                q_s = f"""
                MATCH (n:{node_type} {{user_id: $uid}})
                OPTIONAL MATCH (n)-[r]->(s:Sphere {{user_id: $uid}})
                RETURN n.name AS name, s.name AS sphere, r.weight AS weight
                ORDER BY r.weight DESC
                """
                rows = await self.graph.execute_query(q_s, {"uid": user_id})
                seen_s = set()
                for row in (rows or []):
                    name = row.get("name", "")
                    if name not in seen_s:
                        seen_s.add(name)
                        supports.append({
                            "name": name, "type": node_type,
                            "sphere": row.get("sphere", ""),
                            "weight": row.get("weight", 0.5),
                        })
        except Exception:
            pass
        return blockers, supports

    async def _get_recent_weight_changes(self, user_id: str) -> list[dict]:
        try:
            q, p = graph_queries.get_weight_history(user_id, limit=5)
            rows = await self.graph.execute_query(q, p)
            return [
                {
                    "from_name": r.get("from_name", ""),
                    "to_name": r.get("to_name", ""),
                    "delta": r.get("delta", 0),
                    "from_label": r.get("from_label", ""),
                }
                for r in (rows or [])
            ]
        except Exception:
            return []

    async def _get_last_checkin(self, user_id: str) -> str | None:
        try:
            q, p = graph_queries.get_recent_checkins(user_id, limit=1)
            rows = await self.graph.execute_query(q, p)
            return rows[0].get("summary", "") if rows else None
        except Exception:
            return None
