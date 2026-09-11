from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gremlin_python.process.graph_traversal import __

from connections import gremlin_g, neo4j_driver


def cypher_upsert(person_id: str, name: str) -> str:
    driver = neo4j_driver()
    with driver:
        result = driver.execute_query(
            "MERGE (p:Person {id: $id}) SET p.name = $name RETURN p.id AS id",
            id=person_id,
            name=name,
        )
        return result.records[0]["id"]


def gremlin_upsert(person_id: str, name: str) -> str:
    g, conn = gremlin_g()
    try:
        vertex_id = (
            g.V().has("person", "id", person_id)
            .fold()
            .coalesce(
                __.unfold(),
                __.add_v("person").property("id", person_id),
            )
            .property("name", name)
            .values("id")
            .next()
        )
        return vertex_id
    finally:
        conn.close()


if __name__ == "__main__":
    print("cypher:  ", cypher_upsert("p0", "Person0-Renamed"))
    print("gremlin: ", gremlin_upsert("p0", "Person0-Renamed"))
