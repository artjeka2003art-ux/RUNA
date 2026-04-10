"""All Cypher queries live here. No Cypher anywhere else in the codebase."""


# ── Person ──────────────────────────────────────────────────────────

def get_investment_profile(user_id: str) -> tuple[str, dict]:
    query = """
    MATCH (p:Person {user_id: $user_id})
    RETURN p.investment_profile AS investment_profile
    """
    return query, {"user_id": user_id}


def save_investment_profile(user_id: str, profile_json: str) -> tuple[str, dict]:
    query = """
    MATCH (p:Person {user_id: $user_id})
    SET p.investment_profile = $profile_json, p.updated_at = datetime()
    RETURN p.investment_profile AS investment_profile
    """
    return query, {"user_id": user_id, "profile_json": profile_json}


# ── Promoted document-backed facts ──────────────────────────────────

def get_promoted_facts(user_id: str) -> tuple[str, dict]:
    query = """
    MATCH (p:Person {user_id: $user_id})
    RETURN p.promoted_facts AS promoted_facts
    """
    return query, {"user_id": user_id}


def save_promoted_facts(user_id: str, facts_json: str) -> tuple[str, dict]:
    query = """
    MATCH (p:Person {user_id: $user_id})
    SET p.promoted_facts = $facts_json, p.updated_at = datetime()
    RETURN p.promoted_facts AS promoted_facts
    """
    return query, {"user_id": user_id, "facts_json": facts_json}


def create_person(user_id: str, name: str) -> tuple[str, dict]:
    query = """
    MERGE (p:Person {user_id: $user_id})
    ON CREATE SET p.name = $name, p.created_at = datetime(), p.updated_at = datetime()
    ON MATCH SET p.updated_at = datetime()
    RETURN p
    """
    return query, {"user_id": user_id, "name": name}


# ── Sphere ──────────────────────────────────────────────────────────

def create_sphere(user_id: str, sphere_name: str) -> tuple[str, dict]:
    """Create a sphere. Always creates new node (no MERGE on name).
    For onboarding: uses MERGE to be idempotent on retry."""
    query = """
    MERGE (s:Sphere {user_id: $user_id, name: $sphere_name})
    ON CREATE SET s.created_at = datetime(), s.updated_at = datetime(), s.archived = false
    ON MATCH SET s.updated_at = datetime()
    RETURN s
    """
    return query, {"user_id": user_id, "sphere_name": sphere_name}


# ── Event ───────────────────────────────────────────────────────────

def create_event(user_id: str, name: str, description: str = "") -> tuple[str, dict]:
    query = """
    CREATE (e:Event {
        user_id: $user_id,
        name: $name,
        description: $description,
        created_at: datetime(),
        updated_at: datetime()
    })
    RETURN e
    """
    return query, {"user_id": user_id, "name": name, "description": description}


# ── Pattern ─────────────────────────────────────────────────────────

def create_pattern(user_id: str, name: str, description: str = "") -> tuple[str, dict]:
    query = """
    CREATE (p:Pattern {
        user_id: $user_id,
        name: $name,
        description: $description,
        created_at: datetime(),
        updated_at: datetime()
    })
    RETURN p
    """
    return query, {"user_id": user_id, "name": name, "description": description}


# ── Value ───────────────────────────────────────────────────────────

def create_value(user_id: str, name: str, description: str = "") -> tuple[str, dict]:
    query = """
    CREATE (v:Value {
        user_id: $user_id,
        name: $name,
        description: $description,
        created_at: datetime(),
        updated_at: datetime()
    })
    RETURN v
    """
    return query, {"user_id": user_id, "name": name, "description": description}


# ── Blocker ─────────────────────────────────────────────────────────

def create_blocker(user_id: str, name: str, description: str = "") -> tuple[str, dict]:
    query = """
    CREATE (b:Blocker {
        user_id: $user_id,
        name: $name,
        description: $description,
        created_at: datetime(),
        updated_at: datetime()
    })
    RETURN b
    """
    return query, {"user_id": user_id, "name": name, "description": description}


# ── Goal ────────────────────────────────────────────────────────────

def create_goal(user_id: str, name: str, description: str = "") -> tuple[str, dict]:
    query = """
    CREATE (g:Goal {
        user_id: $user_id,
        name: $name,
        description: $description,
        created_at: datetime(),
        updated_at: datetime()
    })
    RETURN g
    """
    return query, {"user_id": user_id, "name": name, "description": description}


# ── CheckIn ─────────────────────────────────────────────────────────

def create_checkin(user_id: str, summary: str) -> tuple[str, dict]:
    query = """
    MATCH (p:Person {user_id: $user_id})
    CREATE (c:CheckIn {
        user_id: $user_id,
        summary: $summary,
        created_at: datetime(),
        updated_at: datetime()
    })
    CREATE (p)-[:CHANGED_ON {weight: 1.0, created_at: datetime()}]->(c)
    RETURN c
    """
    return query, {"user_id": user_id, "summary": summary}


# ── Edges (generic + typed) ─────────────────────────────────────────

def create_edge_by_name(
    user_id: str,
    from_label: str,
    from_name: str,
    to_label: str,
    to_name: str,
    edge_type: str,
    weight: float = 0.5,
) -> tuple[str, dict]:
    """Connect two nodes by their label + name within one user's graph."""
    query = f"""
    MATCH (a:{from_label} {{user_id: $user_id, name: $from_name}})
    MATCH (b:{to_label} {{user_id: $user_id, name: $to_name}})
    MERGE (a)-[r:{edge_type}]->(b)
    ON CREATE SET r.weight = $weight, r.created_at = datetime()
    ON MATCH SET r.weight = $weight, r.updated_at = datetime()
    RETURN r
    """
    return query, {
        "user_id": user_id,
        "from_name": from_name,
        "to_name": to_name,
        "weight": weight,
    }


def connect_person_to_sphere(user_id: str, sphere_name: str, weight: float = 0.5) -> tuple[str, dict]:
    query = """
    MATCH (p:Person {user_id: $user_id})
    MATCH (s:Sphere {user_id: $user_id, name: $sphere_name})
    MERGE (p)-[r:AFFECTS]->(s)
    ON CREATE SET r.weight = $weight, r.created_at = datetime()
    ON MATCH SET r.weight = $weight, r.updated_at = datetime()
    RETURN r
    """
    return query, {"user_id": user_id, "sphere_name": sphere_name, "weight": weight}


# ── Reads ────────────────────────────────────────────────────────────

def get_user_graph(user_id: str) -> tuple[str, dict]:
    query = """
    MATCH (n {user_id: $user_id})-[r]->(m {user_id: $user_id})
    RETURN labels(n) AS from_labels, n.name AS from_name,
           type(r) AS edge_type, r.weight AS weight,
           labels(m) AS to_labels, m.name AS to_name
    """
    return query, {"user_id": user_id}


def get_spheres(user_id: str) -> tuple[str, dict]:
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    RETURN s.name AS name
    """
    return query, {"user_id": user_id}


def get_sphere_connections(user_id: str, sphere_name: str) -> tuple[str, dict]:
    """Get all nodes connected to a sphere and their edge weights."""
    query = """
    MATCH (s:Sphere {user_id: $user_id, name: $sphere_name})<-[r]-(n {user_id: $user_id})
    RETURN labels(n) AS node_labels, n.name AS node_name,
           type(r) AS edge_type, r.weight AS weight
    """
    return query, {"user_id": user_id, "sphere_name": sphere_name}


def get_recent_checkins(user_id: str, limit: int = 7) -> tuple[str, dict]:
    query = """
    MATCH (c:CheckIn {user_id: $user_id})
    RETURN c.summary AS summary, c.created_at AS created_at
    ORDER BY c.created_at DESC
    LIMIT $limit
    """
    return query, {"user_id": user_id, "limit": limit}


def get_user_nodes_by_type(user_id: str, node_type: str) -> tuple[str, dict]:
    query = f"""
    MATCH (n:{node_type} {{user_id: $user_id}})
    RETURN n.name AS name, n.description AS description
    """
    return query, {"user_id": user_id}


def update_edge_weight(
    user_id: str,
    from_label: str,
    from_name: str,
    to_label: str,
    to_name: str,
    edge_type: str,
    weight: float,
) -> tuple[str, dict]:
    query = f"""
    MATCH (a:{from_label} {{user_id: $user_id, name: $from_name}})
          -[r:{edge_type}]->
          (b:{to_label} {{user_id: $user_id, name: $to_name}})
    SET r.weight = $weight, r.updated_at = datetime()
    RETURN r
    """
    return query, {
        "user_id": user_id,
        "from_name": from_name,
        "to_name": to_name,
        "weight": weight,
    }


# ── Weight History (for prediction math) ──────────────────────────

def log_weight_change(
    user_id: str,
    from_label: str,
    from_name: str,
    to_label: str,
    to_name: str,
    edge_type: str,
    old_weight: float,
    new_weight: float,
) -> tuple[str, dict]:
    """Log every weight change as a WeightLog node. This is the data
    that prediction math uses to calculate momentum and trends."""
    query = """
    CREATE (wl:WeightLog {
        user_id: $user_id,
        from_label: $from_label,
        from_name: $from_name,
        to_label: $to_label,
        to_name: $to_name,
        edge_type: $edge_type,
        old_weight: $old_weight,
        new_weight: $new_weight,
        delta: $delta,
        created_at: datetime()
    })
    RETURN wl
    """
    return query, {
        "user_id": user_id,
        "from_label": from_label,
        "from_name": from_name,
        "to_label": to_label,
        "to_name": to_name,
        "edge_type": edge_type,
        "old_weight": old_weight,
        "new_weight": new_weight,
        "delta": new_weight - old_weight,
    }


def get_weight_history(user_id: str, limit: int = 100) -> tuple[str, dict]:
    """Get all weight changes for prediction math. Ordered by time."""
    query = """
    MATCH (wl:WeightLog {user_id: $user_id})
    RETURN wl.from_label AS from_label, wl.from_name AS from_name,
           wl.to_label AS to_label, wl.to_name AS to_name,
           wl.edge_type AS edge_type,
           wl.old_weight AS old_weight, wl.new_weight AS new_weight,
           wl.delta AS delta, wl.created_at AS created_at
    ORDER BY wl.created_at ASC
    LIMIT $limit
    """
    return query, {"user_id": user_id, "limit": limit}


def get_edge_weight_history(
    user_id: str,
    from_name: str,
    to_name: str,
) -> tuple[str, dict]:
    """Get weight history for a specific edge (for trend calculation)."""
    query = """
    MATCH (wl:WeightLog {user_id: $user_id, from_name: $from_name, to_name: $to_name})
    RETURN wl.old_weight AS old_weight, wl.new_weight AS new_weight,
           wl.delta AS delta, wl.created_at AS created_at
    ORDER BY wl.created_at ASC
    """
    return query, {"user_id": user_id, "from_name": from_name, "to_name": to_name}


def get_sphere_full_data(user_id: str, sphere_name: str) -> tuple[str, dict]:
    """Get sphere with all connected nodes, their types, weights, and descriptions."""
    query = """
    MATCH (s:Sphere {user_id: $user_id, name: $sphere_name})<-[r]-(n {user_id: $user_id})
    RETURN labels(n) AS node_labels, n.name AS node_name, n.description AS description,
           type(r) AS edge_type, r.weight AS weight
    """
    return query, {"user_id": user_id, "sphere_name": sphere_name}


# ── Sphere CRUD (Phase A) ─────────────────────────────────────────

def get_spheres_with_ids(user_id: str) -> tuple[str, dict]:
    """Get all non-archived spheres with elementId for frontend."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE NOT coalesce(s.archived, false)
    RETURN elementId(s) AS id, s.name AS name,
           coalesce(s.description, '') AS description
    ORDER BY s.created_at
    """
    return query, {"user_id": user_id}


def get_sphere_by_id(user_id: str, sphere_id: str) -> tuple[str, dict]:
    """Get a single sphere by its elementId. Ownership-safe."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE elementId(s) = $sphere_id AND NOT coalesce(s.archived, false)
    RETURN elementId(s) AS id, s.name AS name, s.user_id AS user_id,
           coalesce(s.description, '') AS description
    """
    return query, {"user_id": user_id, "sphere_id": sphere_id}


def get_sphere_detail(user_id: str, sphere_id: str) -> tuple[str, dict]:
    """Get sphere + all related nodes (blockers, goals, patterns, values)."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE elementId(s) = $sphere_id AND NOT coalesce(s.archived, false)
    OPTIONAL MATCH (n {user_id: $user_id})-[r]->(s)
    RETURN elementId(s) AS id, s.name AS name,
           coalesce(s.description, '') AS description,
           collect(CASE WHEN n IS NOT NULL THEN {
               labels: labels(n),
               name: n.name,
               description: coalesce(n.description, ''),
               weight: r.weight,
               edge_type: type(r)
           } END) AS related
    """
    return query, {"user_id": user_id, "sphere_id": sphere_id}


def get_related_spheres(user_id: str, sphere_id: str) -> tuple[str, dict]:
    """Find other spheres connected through shared nodes."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE elementId(s) = $sphere_id
    MATCH (n {user_id: $user_id})-[]->(s)
    MATCH (n)-[]->(other:Sphere {user_id: $user_id})
    WHERE other <> s AND NOT coalesce(other.archived, false)
    RETURN DISTINCT other.name AS name
    """
    return query, {"user_id": user_id, "sphere_id": sphere_id}


def rename_sphere(user_id: str, sphere_id: str, new_name: str) -> tuple[str, dict]:
    """Ownership-safe rename."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE elementId(s) = $sphere_id
    SET s.name = $new_name, s.updated_at = datetime()
    RETURN elementId(s) AS id, s.name AS name, s.user_id AS user_id
    """
    return query, {"user_id": user_id, "sphere_id": sphere_id, "new_name": new_name}


def archive_sphere(user_id: str, sphere_id: str) -> tuple[str, dict]:
    """Ownership-safe soft-delete."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE elementId(s) = $sphere_id
    SET s.archived = true, s.updated_at = datetime()
    RETURN elementId(s) AS id, s.name AS name
    """
    return query, {"user_id": user_id, "sphere_id": sphere_id}


def create_sphere_with_id(user_id: str, sphere_name: str, description: str = "") -> tuple[str, dict]:
    """Create sphere and return its elementId. Uses MERGE to prevent duplicates."""
    query = """
    MERGE (s:Sphere {user_id: $user_id, name: $sphere_name})
    ON CREATE SET
        s.description = $description,
        s.archived = false,
        s.created_at = datetime(),
        s.updated_at = datetime()
    ON MATCH SET
        s.updated_at = datetime(),
        s.archived = false
    WITH s
    MATCH (p:Person {user_id: $user_id})
    MERGE (p)-[r:AFFECTS]->(s)
    ON CREATE SET r.weight = 0.5, r.created_at = datetime()
    RETURN elementId(s) AS id, s.name AS name
    """
    return query, {"user_id": user_id, "sphere_name": sphere_name, "description": description}


def get_spheres_with_scores_data(user_id: str) -> tuple[str, dict]:
    """Get all non-archived spheres with elementId for compass focus selection."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE NOT coalesce(s.archived, false)
    RETURN elementId(s) AS id, s.name AS name
    ORDER BY s.created_at
    """
    return query, {"user_id": user_id}


def get_recent_weight_changes_detailed(user_id: str, limit: int = 10) -> tuple[str, dict]:
    """Get recent weight changes with full detail for key shift detection."""
    query = """
    MATCH (wl:WeightLog {user_id: $user_id})
    RETURN wl.from_label AS from_label, wl.from_name AS from_name,
           wl.to_label AS to_label, wl.to_name AS to_name,
           wl.edge_type AS edge_type,
           wl.old_weight AS old_weight, wl.new_weight AS new_weight,
           wl.delta AS delta, wl.created_at AS created_at
    ORDER BY wl.created_at DESC
    LIMIT $limit
    """
    return query, {"user_id": user_id, "limit": limit}


def create_action_feedback(
    user_id: str, status: str, one_move: str, sphere_name: str,
) -> tuple[str, dict]:
    """Save one-move feedback as ActionFeedback node."""
    query = """
    CREATE (af:ActionFeedback {
        user_id: $user_id,
        status: $status,
        one_move: $one_move,
        sphere_name: $sphere_name,
        created_at: datetime()
    })
    RETURN af
    """
    return query, {
        "user_id": user_id,
        "status": status,
        "one_move": one_move,
        "sphere_name": sphere_name,
    }


def get_recent_action_feedback(user_id: str, limit: int = 1) -> tuple[str, dict]:
    """Get most recent action feedback to avoid duplicate submissions."""
    query = """
    MATCH (af:ActionFeedback {user_id: $user_id})
    RETURN af.status AS status, af.one_move AS one_move,
           af.sphere_name AS sphere_name, af.created_at AS created_at
    ORDER BY af.created_at DESC
    LIMIT $limit
    """
    return query, {"user_id": user_id, "limit": limit}


def get_spheres_with_descriptions(user_id: str) -> tuple[str, dict]:
    """Get all non-archived spheres with descriptions for prediction context."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE NOT coalesce(s.archived, false)
    RETURN elementId(s) AS id, s.name AS name,
           coalesce(s.description, '') AS description
    ORDER BY s.created_at
    """
    return query, {"user_id": user_id}


def update_sphere_description(user_id: str, sphere_id: str, description: str) -> tuple[str, dict]:
    """Ownership-safe description update."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE elementId(s) = $sphere_id
    SET s.description = $description, s.updated_at = datetime()
    RETURN elementId(s) AS id, s.name AS name, s.description AS description
    """
    return query, {"user_id": user_id, "sphere_id": sphere_id, "description": description}


def get_sphere_structured_data(user_id: str, sphere_id: str) -> tuple[str, dict]:
    """Get structured_data JSON from a sphere."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE elementId(s) = $sphere_id
    RETURN s.structured_data AS structured_data
    """
    return query, {"user_id": user_id, "sphere_id": sphere_id}


def update_sphere_structured_data(user_id: str, sphere_id: str, structured_data: str) -> tuple[str, dict]:
    """Save structured_data JSON string on a sphere node."""
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    WHERE elementId(s) = $sphere_id
    SET s.structured_data = $structured_data, s.updated_at = datetime()
    RETURN elementId(s) AS id, s.name AS name
    """
    return query, {"user_id": user_id, "sphere_id": sphere_id, "structured_data": structured_data}
