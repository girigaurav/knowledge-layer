from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from connections import neo4j_driver

GRAPH_NAME = "compareGraph"


def _project_graph(driver) -> None:
    driver.execute_query(f"CALL gds.graph.drop('{GRAPH_NAME}', false)")
    driver.execute_query(
        f"CALL gds.graph.project('{GRAPH_NAME}', 'Person', "
        "{FOLLOWS: {orientation: 'NATURAL'}})"
    )


def degree_centrality() -> list[dict]:
    driver = neo4j_driver()
    with driver:
        _project_graph(driver)
        result = driver.execute_query(
            f"CALL gds.degree.stream('{GRAPH_NAME}') "
            "YIELD nodeId, score "
            "RETURN gds.util.asNode(nodeId).name AS name, score "
            "ORDER BY score DESC LIMIT 5"
        )
        return [dict(record) for record in result.records]


def pagerank() -> list[dict]:
    driver = neo4j_driver()
    with driver:
        result = driver.execute_query(
            f"CALL gds.pageRank.stream('{GRAPH_NAME}') "
            "YIELD nodeId, score "
            "RETURN gds.util.asNode(nodeId).name AS name, score "
            "ORDER BY score DESC LIMIT 5"
        )
        return [dict(record) for record in result.records]


def community_detection() -> list[dict]:
    driver = neo4j_driver()
    with driver:
        result = driver.execute_query(
            f"CALL gds.louvain.stream('{GRAPH_NAME}') "
            "YIELD nodeId, communityId "
            "RETURN gds.util.asNode(nodeId).name AS name, communityId "
            "ORDER BY communityId"
        )
        return [dict(record) for record in result.records]


if __name__ == "__main__":
    print("degree centrality:", degree_centrality())
    print("pagerank:", pagerank())
    print("community detection:", community_detection())
