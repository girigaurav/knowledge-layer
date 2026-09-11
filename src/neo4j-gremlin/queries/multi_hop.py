from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import P

from connections import gremlin_g, neo4j_driver


def cypher_multi_hop(person_id: str) -> list[str]:
    driver = neo4j_driver()
    with driver:
        result = driver.execute_query(
            "MATCH (a:Person {id: $person_id})-[:FOLLOWS]->()-[:FOLLOWS]->(b:Person) "
            "WHERE b.id <> $person_id "
            "RETURN DISTINCT b.name AS name ORDER BY name",
            person_id=person_id,
        )
        return [record["name"] for record in result.records]


def gremlin_multi_hop(person_id: str) -> list[str]:
    g, conn = gremlin_g()
    try:
        return (
            g.V().has("id", person_id)
            .out("follows").out("follows")
            .where(__.values("id").is_(P.neq(person_id)))
            .dedup()
            .values("name")
            .order()
            .to_list()
        )
    finally:
        conn.close()


if __name__ == "__main__":
    print("cypher:  ", cypher_multi_hop("p0"))
    print("gremlin: ", gremlin_multi_hop("p0"))
