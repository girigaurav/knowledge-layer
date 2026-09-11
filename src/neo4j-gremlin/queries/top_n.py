from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Order

from connections import gremlin_g, neo4j_driver


def cypher_top_n(n: int = 5) -> list[dict]:
    driver = neo4j_driver()
    with driver:
        result = driver.execute_query(
            "MATCH (p:Person)-[:FOLLOWS]->() "
            "RETURN p.name AS name, count(*) AS following "
            "ORDER BY following DESC LIMIT $n",
            n=n,
        )
        return [dict(record) for record in result.records]


def gremlin_top_n(n: int = 5) -> list[dict]:
    g, conn = gremlin_g()
    try:
        return (
            g.V().has_label("person")
            .project("name", "following")
            .by(__.values("name"))
            .by(__.out("follows").count())
            .order().by(__.select("following"), Order.desc)
            .limit(n)
            .to_list()
        )
    finally:
        conn.close()


if __name__ == "__main__":
    print("cypher:  ", cypher_top_n())
    print("gremlin: ", gremlin_top_n())
