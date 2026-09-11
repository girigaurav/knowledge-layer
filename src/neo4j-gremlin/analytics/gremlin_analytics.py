from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import networkx as nx
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Order

from connections import gremlin_g


def degree_centrality() -> list[dict]:
    # Degree centrality has a direct native Gremlin equivalent - no external tool needed.
    g, conn = gremlin_g()
    try:
        return (
            g.V().has_label("person")
            .project("name", "degree")
            .by(__.values("name"))
            .by(__.both_e("follows").count())
            .order().by(__.select("degree"), Order.desc)
            .limit(5)
            .to_list()
        )
    finally:
        conn.close()


def _export_to_networkx() -> "nx.DiGraph":
    g, conn = gremlin_g()
    try:
        edges = (
            g.V().has_label("person").as_("a")
            .out("follows").as_("b")
            .select("a", "b")
            .by("name")
            .to_list()
        )
    finally:
        conn.close()

    graph = nx.DiGraph()
    for edge in edges:
        graph.add_edge(edge["a"], edge["b"])
    return graph


def pagerank() -> list[tuple[str, float]]:
    # TinkerPop has no native PageRank step for OLTP graphs (OLAP GraphComputer
    # needs a Hadoop/Spark backend). The realistic developer path is exporting
    # the relevant subgraph and running it externally.
    graph = _export_to_networkx()
    scores = nx.pagerank(graph)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:5]


def community_detection() -> list[set[str]]:
    # Same gap as pagerank(): no native Gremlin step, fall back to networkx.
    graph = _export_to_networkx()
    communities = nx.community.greedy_modularity_communities(graph.to_undirected())
    return [set(community) for community in communities]


if __name__ == "__main__":
    print("degree centrality:", degree_centrality())
    print("pagerank (via networkx export):", pagerank())
    print("community detection (via networkx export):", community_detection())
