"""All Cypher queries live here. No Cypher anywhere else in the codebase."""


# ── Person ──────────────────────────────────────────────────────────

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
    query = """
    MERGE (s:Sphere {user_id: $user_id, name: $sphere_name})
    ON CREATE SET s.created_at = datetime(), s.updated_at = datetime()
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
