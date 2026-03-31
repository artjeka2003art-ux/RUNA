import json
import re
from pathlib import Path

from backend.constants import AI_MODEL
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.graph_builder import GraphBuilder
from backend.graph import graph_queries

ANALYST_PROMPT_TEMPLATE = (Path(__file__).parent.parent / "prompts" / "analyst_prompt.txt").read_text()


class AnalystAgent:
    """Reads the personal knowledge graph, updates edge weights based on new data."""

    def __init__(self, ai_client, graph_client: Neo4jClient, graph_builder: GraphBuilder):
        self.ai = ai_client
        self.graph = graph_client
        self.graph_builder = graph_builder
        self.model = AI_MODEL

    async def run_after_checkin(self, user_id: str, user_message: str, companion_reply: str) -> dict:
        """Main entry point: analyze check-in and update the graph."""
        graph_state = await self._build_graph_state(user_id)
        analysis = await self._call_ai(graph_state, user_message, companion_reply)

        if not analysis:
            return {"changes": 0, "details": "no analysis produced"}

        return await self._apply_analysis(user_id, analysis)

    async def _build_graph_state(self, user_id: str) -> str:
        """Read the full graph and format as readable text."""
        lines = []

        query, params = graph_queries.get_user_graph(user_id)
        edges = await self.graph.execute_query(query, params)

        if edges:
            lines.append("=== EDGES ===")
            for e in edges:
                from_labels = e.get("from_labels", [])
                from_name = e.get("from_name", "?")
                to_labels = e.get("to_labels", [])
                to_name = e.get("to_name", "?")
                edge_type = e.get("edge_type", "?")
                weight = e.get("weight", "?")
                from_label = from_labels[0] if from_labels else "?"
                to_label = to_labels[0] if to_labels else "?"
                lines.append(f"  ({from_label}:{from_name}) -[{edge_type} w={weight}]-> ({to_label}:{to_name})")

        for node_type in ["Sphere", "Event", "Pattern", "Value", "Blocker", "Goal"]:
            query, params = graph_queries.get_user_nodes_by_type(user_id, node_type)
            nodes = await self.graph.execute_query(query, params)
            if nodes:
                lines.append(f"\n=== {node_type.upper()}S ===")
                for n in nodes:
                    desc = n.get("description", "")
                    desc_part = f" — {desc}" if desc else ""
                    lines.append(f"  {n['name']}{desc_part}")

        query, params = graph_queries.get_recent_checkins(user_id, limit=5)
        checkins = await self.graph.execute_query(query, params)
        if checkins:
            lines.append("\n=== RECENT CHECK-INS ===")
            for c in checkins:
                lines.append(f"  - {c.get('summary', '')}")

        return "\n".join(lines) if lines else "Graph is empty."

    async def _call_ai(self, graph_state: str, user_message: str, companion_reply: str) -> dict | None:
        """Send graph + check-in to AI, parse JSON response."""
        prompt = (ANALYST_PROMPT_TEMPLATE
            .replace("{graph_state}", graph_state)
            .replace("{user_message}", user_message)
            .replace("{companion_reply}", companion_reply)
        )

        response = await self.ai.chat.completions.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": "You are a graph analyst. Respond ONLY with the <analysis> JSON block."},
                {"role": "user", "content": prompt},
            ],
        )

        text = response.choices[0].message.content
        # Strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        # Try <analysis> tags first (closing tag may be missing)
        match = re.search(r"<analysis>\s*(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                return result
            except json.JSONDecodeError:
                pass

        # Fallback: try to find JSON object in response
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    async def _apply_analysis(self, user_id: str, analysis: dict) -> dict:
        """Apply AI analysis to the graph."""
        changes = {
            "weights_updated": 0,
            "nodes_created": 0,
            "resolved": 0,
            "details": [],
        }

        # 1. Update edge weights + log every change for prediction math
        for update in analysis.get("weight_updates", []):
            try:
                new_weight = max(0.0, min(1.0, update["new_weight"]))
                old_weight = update.get("old_weight", 0.5)

                query, params = graph_queries.update_edge_weight(
                    user_id=user_id,
                    from_label=update["from_label"],
                    from_name=update["from_name"],
                    to_label=update["to_label"],
                    to_name=update["to_name"],
                    edge_type=update["edge_type"],
                    weight=new_weight,
                )
                result = await self.graph.execute_query(query, params)

                if result:
                    log_q, log_p = graph_queries.log_weight_change(
                        user_id=user_id,
                        from_label=update["from_label"],
                        from_name=update["from_name"],
                        to_label=update["to_label"],
                        to_name=update["to_name"],
                        edge_type=update["edge_type"],
                        old_weight=old_weight,
                        new_weight=new_weight,
                    )
                    await self.graph.execute_query(log_q, log_p)

                    changes["weights_updated"] += 1
                    changes["details"].append(
                        f"weight: {update['from_name']}->{update['to_name']} {old_weight}->{new_weight} ({update.get('reason', '')})"
                    )
            except Exception:
                pass

        # 2. Create new nodes
        for node in analysis.get("new_nodes", []):
            try:
                node_type = node["type"]
                name = node["name"]
                description = node.get("description", "")
                spheres = node.get("spheres", [])

                if node_type == "Event":
                    await self.graph_builder.add_event(user_id, name, description, spheres)
                elif node_type == "Pattern":
                    await self.graph_builder.add_pattern(user_id, name, description, spheres)
                elif node_type == "Blocker":
                    await self.graph_builder.add_blocker(user_id, name, description, spheres)
                elif node_type == "Goal":
                    await self.graph_builder.add_goal(user_id, name, description, spheres)
                elif node_type == "Value":
                    await self.graph_builder.add_value(user_id, name, description)
                else:
                    continue

                changes["nodes_created"] += 1
                changes["details"].append(f"new {node_type}: {name}")
            except Exception:
                pass

        # 3. Resolve blockers/patterns (set weight to near zero)
        for resolved in analysis.get("resolved", []):
            try:
                node_type = resolved["type"]
                node_name = resolved["name"]

                query, params = graph_queries.get_user_graph(user_id)
                all_edges = await self.graph.execute_query(query, params)

                for edge in all_edges:
                    from_labels = edge.get("from_labels", [])
                    from_name = edge.get("from_name", "")
                    if node_type in from_labels and from_name == node_name:
                        to_labels = edge.get("to_labels", [])
                        to_name = edge.get("to_name", "")
                        edge_type = edge.get("edge_type", "")
                        query2, params2 = graph_queries.update_edge_weight(
                            user_id=user_id,
                            from_label=node_type,
                            from_name=node_name,
                            to_label=to_labels[0] if to_labels else "Sphere",
                            to_name=to_name,
                            edge_type=edge_type,
                            weight=0.05,
                        )
                        await self.graph.execute_query(query2, params2)

                changes["resolved"] += 1
                changes["details"].append(f"resolved {node_type}: {node_name} ({resolved.get('reason', '')})")
            except Exception:
                pass

        changes["total"] = changes["weights_updated"] + changes["nodes_created"] + changes["resolved"]
        return changes
