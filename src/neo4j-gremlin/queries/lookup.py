from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from connections import gremlin_g, neo4j_driver


def cypher_lookup(community: int) -> list[str]:
    driver = neo4j_driver()
    with driver:
        result = driver.execute_query(
            "MATCH (p:Person) WHERE p.community = $community "
            "RETURN p.name AS name ORDER BY name",
            community=community,
        )
        return [record["name"] for record in result.records]


def gremlin_lookup(community: int) -> list[str]:
    g, conn = gremlin_g()
    try:
        return (
            g.V().has_label("person").has("community", community)
            .values("name")
            .order()
            .to_list()
        )
    finally:
        conn.close()


if __name__ == "__main__":
    print("cypher:  ", cypher_lookup(2))
    print("gremlin: ", gremlin_lookup(2))
