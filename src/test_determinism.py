"""
Determinism check for entity/relationship extraction.

Resets the graph and rebuilds it from data/docs three times against the live
Neo4j + Ollama stack configured in .env, then checks that at least 2 of the
3 runs produced identical entity sets and identical relationship sets.

This is deliberately a live integration test with no mocking - the whole
point is to exercise the real (LLM-driven) extraction path and see whether
build_llm_and_embedder's temperature/seed settings actually hold decoding
steady across independent runs. Expect it to take a few minutes: it performs
3 full reset+rebuild cycles.

Run:
    pytest test_determinism.py -v -s
"""

from __future__ import annotations

import asyncio
from itertools import combinations

import neo4j
import pytest

from graph_rag_pipeline import (
    ONTOLOGY_PATH,
    build_knowledge_graph,
    build_llm_and_embedder,
    ensure_sample_documents,
    load_configuration,
    load_graph_schema,
    reset_graph,
)
from kg_pipeline_cli import read_graph_snapshot

NUM_RUNS = 2


async def _run_all_iterations(
    driver: neo4j.Driver,
    llm,
    embedder,
    schema: dict,
    document_paths: list,
    config,
) -> list[dict[str, set]]:
    snapshots = []
    for run_index in range(NUM_RUNS):
        reset_graph(driver, config.neo4j_database)
        await build_knowledge_graph(
            driver,
            llm,
            embedder,
            schema,
            document_paths,
            config.neo4j_database,
            config.chunk_size,
            config.chunk_overlap,
        )
        snapshot = read_graph_snapshot(driver, config.neo4j_database)
        print(
            f"\nRun {run_index + 1}/{NUM_RUNS}: "
            f"{len(snapshot['entities'])} entities, "
            f"{len(snapshot['relationships'])} relationships"
        )
        snapshots.append(snapshot)
    return snapshots


@pytest.fixture(scope="module")
def multiple_snapshots() -> list[dict[str, set]]:
    config = load_configuration()
    llm, embedder = build_llm_and_embedder(config)
    schema = load_graph_schema(ONTOLOGY_PATH)
    document_paths = ensure_sample_documents()

    with neo4j.GraphDatabase.driver(
        config.neo4j_uri, auth=(config.neo4j_username, config.neo4j_password)
    ) as driver:
        driver.verify_connectivity()
        return asyncio.run(
            _run_all_iterations(driver, llm, embedder, schema, document_paths, config)
        )


def _majority_match(snapshots: list[dict[str, set]], key: str) -> bool:
    return any(
        snapshots[i][key] == snapshots[j][key]
        for i, j in combinations(range(len(snapshots)), 2)
    )


def _print_pairwise_diff(snapshots: list[dict[str, set]], key: str, label: str) -> None:
    print(f"\n{label} differed across all {NUM_RUNS} runs:")
    for i, snapshot in enumerate(snapshots):
        print(f"  Run {i + 1}: {len(snapshot[key])} {label.lower()}")
    for i, j in combinations(range(len(snapshots)), 2):
        only_i = snapshots[i][key] - snapshots[j][key]
        only_j = snapshots[j][key] - snapshots[i][key]
        if not only_i and not only_j:
            continue
        print(f"  Run {i + 1} vs Run {j + 1}:")
        for item in sorted(str(x) for x in only_i):
            print(f"    - only in run {i + 1}: {item}")
        for item in sorted(str(x) for x in only_j):
            print(f"    - only in run {j + 1}: {item}")


def test_entities_majority_match(multiple_snapshots: list[dict[str, set]]) -> None:
    if not _majority_match(multiple_snapshots, "entities"):
        _print_pairwise_diff(multiple_snapshots, "entities", "Entities")
        pytest.fail(f"No two of the {NUM_RUNS} runs produced identical entity sets")


def test_relationships_majority_match(multiple_snapshots: list[dict[str, set]]) -> None:
    if not _majority_match(multiple_snapshots, "relationships"):
        _print_pairwise_diff(multiple_snapshots, "relationships", "Relationships")
        pytest.fail(f"No two of the {NUM_RUNS} runs produced identical relationship sets")
