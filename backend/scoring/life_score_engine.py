from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries
from backend.models.schemas import LifeScore, SphereScore, NextStep


_POSITIVE_TYPES = {"Goal", "Value"}
_NEGATIVE_TYPES = {"Blocker"}
_BASE_SCORE = 50.0
_MAX_SHIFT_PER_NODE = 15.0


def _compute_daily_state(total: float) -> tuple[str, str]:
    if total >= 75:
        return "Устойчивость", "Система видит устойчивые опоры в нескольких сферах."
    if total >= 60:
        return "Восстановление", "Часть опор уже собирается. Одно верное действие в день — достаточно."
    if total >= 45:
        return "Поиск опоры", "Не хаос, но и не точка силы. Выбери одно направление."
    if total >= 30:
        return "Под давлением", "Давление в нескольких сферах. Но есть направление, где можно начать."
    return "Кризис", "Сейчас тяжело. Найдём один маленький шаг."


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
