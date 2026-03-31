"""Scenario Agent — math-first prediction with AI only for narrative.

Architecture:
1. PredictionEngine runs graph math (momentum, projection, probabilities)
2. AI receives the NUMBERS and writes human-readable narratives
3. Prediction = math. Storytelling = AI. Never the other way around.
"""

import json
import re

from backend.constants import AI_MODEL
from backend.graph.neo4j_client import Neo4jClient
from backend.prediction.prediction_engine import PredictionEngine


class ScenarioAgent:
    """Generates prediction scenarios: math for numbers, AI for stories."""

    def __init__(self, ai_client, graph_client: Neo4jClient):
        self.ai = ai_client
        self.graph = graph_client
        self.model = AI_MODEL
        self.prediction_engine = PredictionEngine(graph_client)

    async def generate_scenarios(self, user_id: str, num_weeks: int = 12) -> dict:
        """Generate full prediction report.

        Step 1: Math — PredictionEngine calculates everything from graph data
        Step 2: Narrative — AI turns numbers into human stories
        """
        prediction = await self.prediction_engine.generate_prediction(user_id, num_weeks)

        if prediction.get("error"):
            return prediction

        narratives = await self._generate_narratives(prediction)
        return self._merge_results(prediction, narratives)

    async def _generate_narratives(self, prediction: dict) -> dict:
        """Ask AI to write human-readable stories for the math results."""
        math_summary = self._format_math_for_ai(prediction)

        prompt = f"""You have the results of a mathematical prediction model for one person's life.
The model projected their life graph forward {prediction['weeks_projected']} weeks in 3 scenarios.

YOUR JOB: Write human-readable narratives for each scenario. You are a STORYTELLER, not a predictor.
The numbers are already calculated — don't change them. Just make them into a story this person can understand.

Write in Russian. Be specific, reference the sphere names and node names from the data.

## Math results:
{math_summary}

## Output format — ONLY this JSON inside <narratives> tags:

<narratives>
{{
  "optimistic": {{
    "title": "short title in Russian",
    "narrative": "3-4 sentences describing this future based on the math. Reference specific spheres and their projected scores."
  }},
  "realistic": {{
    "title": "...",
    "narrative": "..."
  }},
  "pessimistic": {{
    "title": "...",
    "narrative": "..."
  }},
  "leverage_point_narrative": "1-2 sentences explaining the key leverage point in human terms",
  "warning_narrative": "1-2 sentences explaining the warning signal in human terms"
}}
</narratives>"""

        try:
            response = await self.ai.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": "You are a narrative writer. You turn math results into human stories. You do NOT predict — the math already did. Respond ONLY with the <narratives> JSON block."},
                    {"role": "user", "content": prompt},
                ],
            )

            text = response.choices[0].message.content
            # Strip markdown code fences
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)

            match = re.search(r"<narratives>\s*(\{.*\})\s*</narratives>", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # Fallback: try raw JSON
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass

        return {}

    def _format_math_for_ai(self, prediction: dict) -> str:
        """Format prediction math results as readable text for AI."""
        lines = []

        for mode in ("optimistic", "realistic", "pessimistic"):
            scenario = prediction["scenarios"].get(mode, {})
            lines.append(f"\n=== {mode.upper()} (probability: {scenario.get('probability', '?')}%) ===")
            lines.append(f"Total score: {scenario.get('total_score_initial', '?')} → {scenario.get('total_score_final', '?')} (delta: {scenario.get('total_delta', '?')})")

            for sp in scenario.get("sphere_projections", []):
                lines.append(f"  {sp['sphere']}: {sp['initial_score']} → {sp['final_score']} (delta: {sp['delta']})")
                for driver in sp.get("key_drivers", []):
                    lines.append(f"    {driver['direction']}: {driver['node']} ({driver['type']}) {driver['weight_change']}")

        leverage = prediction.get("leverage_point", {})
        lines.append(f"\nKey leverage point: {leverage.get('node', '?')} ({leverage.get('type', '?')}) in {leverage.get('sphere', '?')} — {leverage.get('impact', '')}")

        warning = prediction.get("warning_signal", {})
        lines.append(f"Warning signal: {warning.get('node', '?')} ({warning.get('type', '?')}) in {warning.get('sphere', '?')} — {warning.get('trend', '')}")

        return "\n".join(lines)

    def _merge_results(self, prediction: dict, narratives: dict) -> dict:
        """Merge math results with AI narratives into final output."""
        scenarios = []

        for mode in ("optimistic", "realistic", "pessimistic"):
            math = prediction["scenarios"].get(mode, {})
            narr = narratives.get(mode, {})

            scenarios.append({
                "type": mode,
                "title": narr.get("title", mode.capitalize()),
                "narrative": narr.get("narrative", ""),
                "probability": math.get("probability", 33),
                "total_score_initial": math.get("total_score_initial", 50),
                "total_score_final": math.get("total_score_final", 50),
                "total_delta": math.get("total_delta", 0),
                "sphere_projections": math.get("sphere_projections", []),
            })

        return {
            "scenarios": scenarios,
            "key_leverage_point": {
                **prediction.get("leverage_point", {}),
                "narrative": narratives.get("leverage_point_narrative", ""),
            },
            "warning_signal": {
                **prediction.get("warning_signal", {}),
                "narrative": narratives.get("warning_narrative", ""),
            },
            "meta": {
                "weeks_projected": prediction.get("weeks_projected", 12),
                "spheres_analyzed": len(prediction.get("spheres", [])),
                "method": "graph_math",
            },
        }
