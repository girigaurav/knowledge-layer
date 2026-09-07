"""
CLI-shaped alternative to graph_rag_pipeline.py, inspired by the subcommand
structure of Unstructured-Data-to-graph's src/main.py: discrete `ingest` and
`chat` commands instead of one flag-driven script, an ingestion diff report,
and an interactive chat REPL with citations instead of a fixed batch of demo
questions.

This intentionally omits that project's candidate-graph staging, ontology
approval, and publish gating. Ingestion here writes straight to the graph
via SimpleKGPipeline, exactly like graph_rag_pipeline.py - there is no
candidate/production split.

Run:
    python kg_pipeline_cli.py ingest data/docs
    python kg_pipeline_cli.py ingest data/docs --reset
    python kg_pipeline_cli.py chat

Configuration (Neo4j/Ollama credentials, chunk size, ontology path) is
shared with graph_rag_pipeline.py via .env - see that script/README for
details.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

import neo4j

from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.types import RetrieverResultItem

from graph_rag_pipeline import (
    ONTOLOGY_PATH,
    RETRIEVAL_QUERY,
    VECTOR_INDEX_NAME,
    build_knowledge_graph,
    build_llm_and_embedder,
    create_chunk_vector_index,
    load_configuration,
    load_graph_schema,
    reset_graph,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kg_pipeline_cli")

_DIFF_LIST_LIMIT = 20


# ---------------------------------------------------------------------------
# ingest: build the graph, then report what changed
# ---------------------------------------------------------------------------
def read_graph_snapshot(driver: neo4j.Driver, neo4j_database: str | None) -> dict[str, set]:
    records, _, _ = driver.execute_query(
        "MATCH (d:Document) RETURN collect(d.path) AS paths",
        database_=neo4j_database,
    )
    document_paths = set(records[0]["paths"])

    # SimpleKGPipeline tags every node it creates - Chunk, Document, and each
    # extracted entity alike - with an internal __KGBuilder__ label (it's how
    # the pipeline tracks its own writes), and entities also carry a generic
    # __Entity__ label alongside their real type (e.g. Person). Neither is a
    # node category to exclude; they just have to be stripped out of
    # labels(e) to get at the actual type name.
    records, _, _ = driver.execute_query(
        "MATCH (e) WHERE NOT e:Chunk AND NOT e:Document "
        "RETURN collect(DISTINCT ["
        "  [lbl IN labels(e) WHERE NOT lbl IN ['__KGBuilder__', '__Entity__']][0],"
        "  e.name"
        "]) AS entities",
        database_=neo4j_database,
    )
    entities = {tuple(pair) for pair in records[0]["entities"]}

    records, _, _ = driver.execute_query(
        "MATCH (a)-[r]->(b) "
        "WHERE NOT a:Chunk AND NOT a:Document AND NOT b:Chunk AND NOT b:Document "
        "RETURN collect(DISTINCT [a.name, type(r), b.name]) AS relationships",
        database_=neo4j_database,
    )
    relationships = {tuple(triple) for triple in records[0]["relationships"]}

    return {"document_paths": document_paths, "entities": entities, "relationships": relationships}


def _print_diff_section(label: str, added: set, removed: set) -> None:
    def _print_list(sub_label: str, items: set) -> None:
        names = sorted(str(item) for item in items)
        print(f"  {sub_label}: {len(names)}")
        for name in names[:_DIFF_LIST_LIMIT]:
            print(f"    - {name}")
        if len(names) > _DIFF_LIST_LIMIT:
            print(f"    ... and {len(names) - _DIFF_LIST_LIMIT} more")

    print(f"\n{label}")
    _print_list("Added", added)
    _print_list("Removed", removed)


def print_ingestion_diff(before: dict[str, set], after: dict[str, set]) -> None:
    print("\n=== Ingestion Diff Report (vs. graph state before this run) ===")
    print(
        f"Documents: +{len(after['document_paths'] - before['document_paths'])} "
        f"/-{len(before['document_paths'] - after['document_paths'])}"
    )
    print(
        f"Entities: +{len(after['entities'] - before['entities'])} "
        f"/-{len(before['entities'] - after['entities'])}"
    )
    print(
        f"Relationships: +{len(after['relationships'] - before['relationships'])} "
        f"/-{len(before['relationships'] - after['relationships'])}"
    )
    _print_diff_section(
        "Documents", after["document_paths"] - before["document_paths"],
        before["document_paths"] - after["document_paths"],
    )
    _print_diff_section(
        "Entities", after["entities"] - before["entities"],
        before["entities"] - after["entities"],
    )
    _print_diff_section(
        "Relationships", after["relationships"] - before["relationships"],
        before["relationships"] - after["relationships"],
    )
    print(
        "\nNote: only additions/removals are tracked here, not in-place content "
        "changes to an existing document - that needs a persisted content hash "
        "per document, which this single-script pipeline doesn't maintain."
    )


def run_ingest(docs_dir: Path, reset: bool) -> None:
    config = load_configuration()
    llm, embedder = build_llm_and_embedder(config)

    with neo4j.GraphDatabase.driver(
        config.neo4j_uri, auth=(config.neo4j_username, config.neo4j_password)
    ) as driver:
        driver.verify_connectivity()

        before = read_graph_snapshot(driver, config.neo4j_database)

        if reset:
            reset_graph(driver, config.neo4j_database)

        document_paths = sorted(docs_dir.glob("*.md"))
        if not document_paths:
            raise FileNotFoundError(f"No markdown documents found in {docs_dir}.")

        schema = load_graph_schema(ONTOLOGY_PATH)
        asyncio.run(
            build_knowledge_graph(
                driver,
                llm,
                embedder,
                schema,
                document_paths,
                config.neo4j_database,
                config.chunk_size,
                config.chunk_overlap,
            )
        )
        create_chunk_vector_index(driver, embedder, config.neo4j_database)

        after = read_graph_snapshot(driver, config.neo4j_database)
        print_ingestion_diff(before, after)


# ---------------------------------------------------------------------------
# chat: interactive REPL with citations
# ---------------------------------------------------------------------------
def format_retrieval_result(record: neo4j.Record) -> RetrieverResultItem:
    return RetrieverResultItem(
        content=record["chunk_text"],
        metadata={
            "score": record["score"],
            "entities": record["entities"],
            "entity_relationships": record["entity_relationships"],
        },
    )


def print_citations(retriever_result) -> None:
    entities: list[str] = []
    relationships: list[str] = []
    for item in retriever_result.items:
        entities.extend(item.metadata.get("entities") or [])
        relationships.extend(item.metadata.get("entity_relationships") or [])

    entities = [name for name in dict.fromkeys(entities) if name]
    relationships = [rel for rel in dict.fromkeys(relationships) if rel and "-> " != rel[-3:]]

    if not entities and not relationships:
        return
    print("Sources:")
    for name in entities:
        print(f"  - entity: {name}")
    for rel in relationships:
        print(f"  - graph path: {rel}")
    print()


def run_chat() -> None:
    config = load_configuration()
    llm, embedder = build_llm_and_embedder(config)

    with neo4j.GraphDatabase.driver(
        config.neo4j_uri, auth=(config.neo4j_username, config.neo4j_password)
    ) as driver:
        driver.verify_connectivity()

        retriever = VectorCypherRetriever(
            driver,
            index_name=VECTOR_INDEX_NAME,
            retrieval_query=RETRIEVAL_QUERY,
            embedder=embedder,
            neo4j_database=config.neo4j_database,
            result_formatter=format_retrieval_result,
        )
        rag = GraphRAG(retriever=retriever, llm=llm)

        print("=== Ask the Knowledge Graph ===")
        print("Type 'exit' to quit.\n")

        while True:
            try:
                query = input("You: ").strip()
            except EOFError:
                break
            if not query or query.lower() in {"exit", "quit"}:
                break

            result = rag.search(
                query_text=query, retriever_config={"top_k": 5}, return_context=True
            )
            print(f"\nAssistant: {result.answer}\n")
            print_citations(result.retriever_result)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kg_pipeline_cli.py", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Build the graph from a documents directory.")
    ingest_parser.add_argument("docs_dir", help="Directory containing source markdown documents.")
    ingest_parser.add_argument(
        "--reset", action="store_true", help="Delete all graph data before building."
    )

    subparsers.add_parser("chat", help="Ask the knowledge graph questions in an interactive REPL.")

    return parser


def main() -> None:
    args = build_arg_parser().parse_args()

    if args.command == "ingest":
        run_ingest(Path(args.docs_dir), args.reset)
    elif args.command == "chat":
        run_chat()


if __name__ == "__main__":
    main()
