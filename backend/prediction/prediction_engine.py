"""Prediction Engine — generates scenarios from graph math, not LLM guessing.

Flow:
1. Load full graph state (all spheres, edges, weights)
2. Load weight history (all WeightLog nodes)
3. Calculate momentum for every edge (trend from history)
4. Project weights forward for 3 scenarios (optimistic/realistic/pessimistic)
5. Calculate sphere scores at projected states
6. Calculate probabilities based on momentum distribution
7. Pass numbers to Claude ONLY for narrative (storytelling, not prediction)
"""

from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries
from backend.prediction.graph_math import (
    EdgeState,
    SphereState,
    calculate_momentum,
    calculate_sphere_score,
    project_sphere,
    calculate_scenario_probability,
)


class PredictionEngine:
    """Orchestrates prediction: graph data → math → projected scenarios."""

    def __init__(self, graph_client: Neo4jClient):
        self.graph = graph_client

    async def generate_prediction(self, user_id: str, weeks: int = 12) -> dict:
        """Generate full prediction with 3 scenarios.

        Returns raw math results — no LLM involved.
        """
        # 1. Build sphere states with momentum from weight history
        spheres = await self._build_sphere_states(user_id)

        if not spheres:
            return {"scenarios": [], "error": "no_data"}

        # 2. Project each scenario
        scenarios = {}
        for mode in ("optimistic", "realistic", "pessimistic"):
            scenario_spheres = []
            for sphere in spheres:
                projected = project_sphere(sphere, weeks, mode)
                scenario_spheres.append(projected)

            probability = calculate_scenario_probability(spheres, mode, weeks)

            total_initial = sum(s.score for s in spheres) / len(spheres)
            total_final = sum(ps["final_score"] for ps in scenario_spheres) / len(scenario_spheres)

            scenarios[mode] = {
                "type": mode,
                "sphere_projections": scenario_spheres,
                "total_score_initial": round(total_initial, 1),
                "total_score_final": round(total_final, 1),
                "total_delta": round(total_final - total_initial, 1),
                "probability": probability,
            }

        # 3. Normalize probabilities to sum to 100
        total_prob = sum(s["probability"] for s in scenarios.values())
        if total_prob > 0:
            for s in scenarios.values():
                s["probability"] = round(s["probability"] * 100 / total_prob, 1)

        # 4. Find key leverage point (the edge with most impact potential)
        leverage = self._find_leverage_point(spheres)

        # 5. Find warning signal (edge trending worst)
        warning = self._find_warning_signal(spheres)

        return {
            "scenarios": scenarios,
            "spheres": [
                {
                    "name": s.name,
                    "current_score": round(s.score, 1),
                    "momentum": round(s.momentum, 4),
                    "edge_count": len(s.edges),
                }
                for s in spheres
            ],
            "leverage_point": leverage,
            "warning_signal": warning,
            "weeks_projected": weeks,
        }

    async def _build_sphere_states(self, user_id: str) -> list[SphereState]:
        """Load graph + weight history and build SphereState objects."""

        # Get all spheres
        query, params = graph_queries.get_spheres(user_id)
        sphere_rows = await self.graph.execute_query(query, params)
        if not sphere_rows:
            return []

        # Load full weight history
        query, params = graph_queries.get_weight_history(user_id, limit=500)
        history_rows = await self.graph.execute_query(query, params)

        # Index history by edge key → list of deltas
        history_index: dict[str, list[float]] = {}
        for row in history_rows:
            key = f"{row['from_name']}→{row['to_name']}"
            if key not in history_index:
                history_index[key] = []
            history_index[key].append(row["delta"])

        # Build sphere states
        spheres = []
        for sphere_row in sphere_rows:
            sphere_name = sphere_row["name"]

            # Get all connections to this sphere
            query, params = graph_queries.get_sphere_full_data(user_id, sphere_name)
            connections = await self.graph.execute_query(query, params)

            edges = []
            for conn in (connections or []):
                node_labels = conn.get("node_labels", [])
                from_label = node_labels[0] if node_labels else "Unknown"
                from_name = conn.get("node_name", "")
                weight = conn.get("weight", 0.5)

                # Get momentum from history
                key = f"{from_name}→{sphere_name}"
                deltas = history_index.get(key, [])
                momentum = calculate_momentum(deltas)

                edges.append(EdgeState(
                    from_label=from_label,
                    from_name=from_name,
                    to_label="Sphere",
                    to_name=sphere_name,
                    edge_type=conn.get("edge_type", "AFFECTS"),
                    weight=weight,
                    momentum=momentum,
                    history=[d for d in deltas],
                ))

            score = calculate_sphere_score(edges)

            # Overall sphere momentum = weighted average of edge momentums
            if edges:
                sphere_momentum = sum(e.momentum * e.weight for e in edges) / sum(e.weight for e in edges)
            else:
                sphere_momentum = 0.0

            spheres.append(SphereState(
                name=sphere_name,
                score=score,
                edges=edges,
                momentum=sphere_momentum,
            ))

        return spheres

    def _find_leverage_point(self, spheres: list[SphereState]) -> dict:
        """Find the single edge that would most improve the overall score.

        Logic: find the highest-weight Blocker (biggest negative impact)
        or lowest-momentum Goal (most stalled progress).
        """
        worst_blocker = None
        worst_weight = 0.0

        for sphere in spheres:
            for edge in sphere.edges:
                if edge.from_label == "Blocker" and edge.weight > worst_weight:
                    worst_weight = edge.weight
                    worst_blocker = {
                        "node": edge.from_name,
                        "type": "Blocker",
                        "sphere": sphere.name,
                        "weight": round(edge.weight, 2),
                        "impact": f"Снижает {sphere.name} на {round(edge.weight * 15, 1)} очков",
                    }

        if worst_blocker:
            return worst_blocker

        # No blockers — find the Goal with lowest progress
        weakest_goal = None
        weakest_weight = 1.0

        for sphere in spheres:
            for edge in sphere.edges:
                if edge.from_label == "Goal" and edge.weight < weakest_weight:
                    weakest_weight = edge.weight
                    weakest_goal = {
                        "node": edge.from_name,
                        "type": "Goal",
                        "sphere": sphere.name,
                        "weight": round(edge.weight, 2),
                        "impact": f"Продвижение к этой цели поднимет {sphere.name}",
                    }

        return weakest_goal or {"node": "—", "type": "none", "impact": "Недостаточно данных"}

    def _find_warning_signal(self, spheres: list[SphereState]) -> dict:
        """Find the edge with the worst negative trend."""
        worst_edge = None
        worst_momentum = 0.0

        for sphere in spheres:
            for edge in sphere.edges:
                # For blockers: positive momentum is bad (blocker growing)
                if edge.from_label == "Blocker" and edge.momentum > worst_momentum:
                    worst_momentum = edge.momentum
                    worst_edge = {
                        "node": edge.from_name,
                        "type": "Blocker",
                        "sphere": sphere.name,
                        "trend": f"Усиливается ({round(edge.momentum, 3)}/чекин)",
                    }
                # For goals/values: negative momentum is bad
                elif edge.from_label in ("Goal", "Value") and edge.momentum < -worst_momentum:
                    worst_momentum = abs(edge.momentum)
                    worst_edge = {
                        "node": edge.from_name,
                        "type": edge.from_label,
                        "sphere": sphere.name,
                        "trend": f"Теряет вес ({round(edge.momentum, 3)}/чекин)",
                    }

        return worst_edge or {"node": "—", "type": "none", "trend": "Нет тревожных сигналов"}
