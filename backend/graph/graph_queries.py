"""All Cypher queries live here. No Cypher anywhere else in the codebase."""


def create_person(user_id: str, name: str) -> tuple[str, dict]:
    query = """
    CREATE (p:Person {
        user_id: $user_id,
        name: $name,
        created_at: datetime(),
        updated_at: datetime()
    })
    RETURN p
    """
    return query, {"user_id": user_id, "name": name}


def create_sphere(user_id: str, sphere_name: str) -> tuple[str, dict]:
    query = """
    CREATE (s:Sphere {
        user_id: $user_id,
        name: $sphere_name,
        created_at: datetime(),
        updated_at: datetime()
    })
    RETURN s
    """
    return query, {"user_id": user_id, "sphere_name": sphere_name}


def create_edge(from_id: str, to_id: str, edge_type: str, weight: float = 0.5) -> tuple[str, dict]:
    query = f"""
    MATCH (a {{user_id: $from_id}}), (b {{user_id: $to_id}})
    CREATE (a)-[r:{edge_type} {{weight: $weight, created_at: datetime()}}]->(b)
    RETURN r
    """
    return query, {"from_id": from_id, "to_id": to_id, "weight": weight}


def get_user_graph(user_id: str) -> tuple[str, dict]:
    query = """
    MATCH (n {user_id: $user_id})-[r]-(m {user_id: $user_id})
    RETURN n, r, m
    """
    return query, {"user_id": user_id}


def get_spheres(user_id: str) -> tuple[str, dict]:
    query = """
    MATCH (s:Sphere {user_id: $user_id})
    RETURN s
    """
    return query, {"user_id": user_id}


def update_edge_weight(from_id: str, to_id: str, edge_type: str, weight: float) -> tuple[str, dict]:
    query = f"""
    MATCH (a {{user_id: $from_id}})-[r:{edge_type}]->(b {{user_id: $to_id}})
    SET r.weight = $weight, r.updated_at = datetime()
    RETURN r
    """
    return query, {"from_id": from_id, "to_id": to_id, "weight": weight}


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
