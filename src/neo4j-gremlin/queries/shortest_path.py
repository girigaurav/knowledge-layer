from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gremlin_python.process.graph_traversal import __

from connections import gremlin_g, neo4j_driver


def cypher_shortest_path(from_id: str, to_id: str) -> list[str]:
    driver = neo4j_driver()
    with driver:
        result = driver.execute_query(
            "MATCH p = shortestPath((a:Person {id: $from_id})-[:FOLLOWS*]-(b:Person {id: $to_id})) "
            "RETURN [n IN nodes(p) | n.name] AS names",
            from_id=from_id,
            to_id=to_id,
        )
        return result.records[0]["names"] if result.records else []


def gremlin_shortest_path(from_id: str, to_id: str) -> list[str]:
    # TinkerPop has a shortestPath() step, but its config-object API
    # (ShortestPath.target / ShortestPath.edges via .with_()) is awkward enough
    # that most Gremlin devs reach for a manual repeat/until BFS instead.
    g, conn = gremlin_g()
    try:
        path = (
            g.V().has("id", from_id)
            .repeat(__.both("follows").simple_path())
            .until(__.has("id", to_id))
            .limit(1)
            .path()
            .by("name")
            .next()
        )
        return list(path)
    finally:
        conn.close()


if __name__ == "__main__":
    print("cypher:  ", cypher_shortest_path("p0", "p13"))
    print("gremlin: ", gremlin_shortest_path("p0", "p13"))
