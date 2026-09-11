from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Order

from connections import gremlin_g, neo4j_driver


def cypher_aggregation() -> list[dict]:
    driver = neo4j_driver()
    with driver:
        result = driver.execute_query(
            "MATCH (:Person)-[r:PURCHASED]->(p:Product) "
            "RETURN p.name AS product, count(r) AS orders, sum(r.quantity) AS units "
            "ORDER BY units DESC"
        )
        return [dict(record) for record in result.records]


def gremlin_aggregation() -> list[dict]:
    g, conn = gremlin_g()
    try:
        return (
            g.V().has_label("product")
            .project("product", "orders", "units")
            .by(__.values("name"))
            .by(__.in_e("purchased").count())
            .by(__.in_e("purchased").values("quantity").sum_())
            .order().by(__.select("units"), Order.desc)
            .to_list()
        )
    finally:
        conn.close()


if __name__ == "__main__":
    print("cypher:  ", cypher_aggregation())
    print("gremlin: ", gremlin_aggregation())
