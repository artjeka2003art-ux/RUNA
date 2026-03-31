"""Graph Math — mathematical prediction based on real graph data.

No LLM calls. No guessing. Pure math on weighted edges.

Core concepts:
- Momentum: how fast a weight is changing (trend from weight history)
- Propagation: how influence flows through edges (blocker affects sphere,
  sphere affects goals connected to it)
- Projection: extrapolate current trends into the future with 3 scenarios
- Probability: based on ratio of positive vs negative momentum
"""

from dataclasses import dataclass, field


@dataclass
class EdgeState:
    """Current state of one edge in the graph."""
    from_label: str
    from_name: str
    to_label: str
    to_name: str
    edge_type: str
    weight: float
    momentum: float = 0.0  # Average delta per check-in (positive = improving)
    history: list[float] = field(default_factory=list)  # Weight values over time


@dataclass
class SphereState:
    """Calculated state of one life sphere."""
    name: str
    score: float
    edges: list[EdgeState] = field(default_factory=list)
    momentum: float = 0.0  # Overall momentum (weighted average of edge momentums)


def calculate_momentum(deltas: list[float]) -> float:
    """Calculate momentum from a list of weight deltas.

    Uses exponential weighting — recent changes matter more than old ones.
    Returns average weighted delta.
    """
    if not deltas:
        return 0.0

    # Exponential decay: most recent change has weight 1.0, oldest has ~0.3
    total = 0.0
    weight_sum = 0.0

    for i, delta in enumerate(deltas):
        # More recent = higher weight
        w = 0.3 + 0.7 * (i / max(len(deltas) - 1, 1))
        total += delta * w
        weight_sum += w

    return total / weight_sum if weight_sum > 0 else 0.0


def calculate_sphere_score(edges: list[EdgeState]) -> float:
    """Calculate sphere score from its edges.

    Same logic as LifeScoreEngine but works on EdgeState objects.
    """
    score = 50.0

    for edge in edges:
        shift = edge.weight * 15.0

        if edge.from_label in ("Goal", "Value"):
            score += shift
        elif edge.from_label == "Blocker":
            score -= shift
        else:  # Pattern, Event
            score += shift * 0.2

    return max(0.0, min(100.0, score))


def project_weight(current: float, momentum: float, weeks: int, mode: str) -> float:
    """Project a weight into the future based on momentum and scenario mode.

    Modes:
    - optimistic: positive momentum x1.5, negative momentum x0.5
    - realistic: momentum x1.0
    - pessimistic: positive momentum x0.5, negative momentum x1.5
    """
    mode_multipliers = {
        "optimistic": (1.5, 0.5),   # (positive_mult, negative_mult)
        "realistic": (1.0, 1.0),
        "pessimistic": (0.5, 1.5),
    }

    pos_mult, neg_mult = mode_multipliers.get(mode, (1.0, 1.0))

    projected = current
    for _ in range(weeks):
        if momentum >= 0:
            projected += momentum * pos_mult
        else:
            projected += momentum * neg_mult

        # Dampen momentum over time (diminishing returns)
        momentum *= 0.9

    return max(0.0, min(1.0, projected))


def project_sphere(sphere: SphereState, weeks: int, mode: str) -> dict:
    """Project a sphere's score into the future.

    Returns week-by-week scores and final state.
    """
    # Project each edge's weight
    projected_edges = []
    weekly_scores = []

    for week in range(1, weeks + 1):
        week_edges = []
        for edge in sphere.edges:
            proj_weight = project_weight(edge.weight, edge.momentum, week, mode)
            week_edges.append(EdgeState(
                from_label=edge.from_label,
                from_name=edge.from_name,
                to_label=edge.to_label,
                to_name=edge.to_name,
                edge_type=edge.edge_type,
                weight=proj_weight,
                momentum=edge.momentum,
            ))

        week_score = calculate_sphere_score(week_edges)
        weekly_scores.append(round(week_score, 1))

        if week == weeks:
            projected_edges = week_edges

    final_score = weekly_scores[-1] if weekly_scores else sphere.score

    return {
        "sphere": sphere.name,
        "initial_score": round(sphere.score, 1),
        "final_score": round(final_score, 1),
        "delta": round(final_score - sphere.score, 1),
        "weekly_scores": weekly_scores,
        "key_drivers": _identify_key_drivers(projected_edges, sphere.edges),
    }


def _identify_key_drivers(projected: list[EdgeState], original: list[EdgeState]) -> list[dict]:
    """Identify which nodes caused the biggest score change."""
    drivers = []

    orig_map = {(e.from_name, e.to_name): e.weight for e in original}

    for edge in projected:
        key = (edge.from_name, edge.to_name)
        orig_weight = orig_map.get(key, 0.5)
        delta = edge.weight - orig_weight

        if abs(delta) > 0.05:  # Only significant changes
            direction = "улучшение" if (
                (edge.from_label in ("Goal", "Value") and delta > 0) or
                (edge.from_label == "Blocker" and delta < 0)
            ) else "ухудшение"

            drivers.append({
                "node": edge.from_name,
                "type": edge.from_label,
                "weight_change": f"{orig_weight:.2f} → {edge.weight:.2f}",
                "direction": direction,
            })

    # Sort by absolute impact
    drivers.sort(key=lambda d: abs(float(d["weight_change"].split(" → ")[1]) - float(d["weight_change"].split(" → ")[0])), reverse=True)
    return drivers[:5]


def calculate_scenario_probability(
    spheres: list[SphereState],
    mode: str,
    weeks: int = 12,
) -> float:
    """Calculate probability of a scenario based on current graph data.

    Logic:
    - Count positive vs negative momentum across all edges
    - High positive momentum = optimistic more likely
    - High negative momentum = pessimistic more likely
    - Mixed/low momentum = realistic most likely

    No LLM. Just math.
    """
    total_positive_momentum = 0.0
    total_negative_momentum = 0.0
    edge_count = 0

    for sphere in spheres:
        for edge in sphere.edges:
            edge_count += 1
            if edge.from_label in ("Goal", "Value"):
                # For positive nodes: positive momentum = good
                if edge.momentum > 0:
                    total_positive_momentum += edge.momentum
                else:
                    total_negative_momentum += abs(edge.momentum)
            elif edge.from_label == "Blocker":
                # For blockers: negative momentum = good (blocker weakening)
                if edge.momentum < 0:
                    total_positive_momentum += abs(edge.momentum)
                else:
                    total_negative_momentum += edge.momentum
            else:
                # Patterns/Events: any momentum is mildly positive
                total_positive_momentum += abs(edge.momentum) * 0.2

    if edge_count == 0:
        # No data — equal probabilities
        return {"optimistic": 25, "realistic": 50, "pessimistic": 25}[mode]

    # Normalize
    total = total_positive_momentum + total_negative_momentum
    if total == 0:
        # No momentum at all — realistic dominates
        return {"optimistic": 20, "realistic": 55, "pessimistic": 25}[mode]

    positive_ratio = total_positive_momentum / total  # 0 to 1

    # Map ratio to probabilities
    # positive_ratio = 1.0 → optimistic ~50%, realistic ~35%, pessimistic ~15%
    # positive_ratio = 0.5 → optimistic ~25%, realistic ~45%, pessimistic ~30%
    # positive_ratio = 0.0 → optimistic ~10%, realistic ~35%, pessimistic ~55%

    if mode == "optimistic":
        prob = 10 + positive_ratio * 40  # 10-50
    elif mode == "realistic":
        prob = 35 + (0.5 - abs(positive_ratio - 0.5)) * 20  # 35-45
    else:  # pessimistic
        prob = 10 + (1 - positive_ratio) * 40  # 10-50

    return round(max(10, min(55, prob)), 1)
