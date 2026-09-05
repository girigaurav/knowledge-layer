"""
GraphRAG pipeline over a local Neo4j + Ollama stack.

Follows the neo4j-graphrag-python "Knowledge Graph Builder" guide
(https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html#data-loader):
markdown files on disk -> DataLoader -> text splitter -> entity/relation
extraction (LLM) -> Neo4j graph writer, followed by a vector index and a
GraphRAG retriever for question answering.

Run:
    python graph_rag_pipeline.py
    python graph_rag_pipeline.py --reset
    python graph_rag_pipeline.py --skip-build
    python graph_rag_pipeline.py --question "Who leads the Perception Team?"

Chunking is controlled via the CHUNK_SIZE / CHUNK_OVERLAP environment
variables (see .env), not command-line flags.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import neo4j
from dotenv import load_dotenv

from neo4j_graphrag.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)
from neo4j_graphrag.embeddings.ollama import OllamaEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.llm.ollama_llm import OllamaLLM
from neo4j_graphrag.retrievers import VectorCypherRetriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("graph_rag_pipeline")

DATA_DIR = Path(__file__).parent / "data" / "docs"
VECTOR_INDEX_NAME = "chunk_embeddings"
CHUNK_NODE_LABEL = "Chunk"
CHUNK_EMBEDDING_PROPERTY = "embedding"

# `node` is the Chunk bound by the vector search; walk out to the entities
# extracted from it (entity)-[:FROM_CHUNK]->(node) and one hop further to
# their graph neighborhood, so retrieval surfaces the entity graph around a
# matched chunk, not just the chunk's raw text.
RETRIEVAL_QUERY = """
OPTIONAL MATCH (entity)-[:FROM_CHUNK]->(node)
WHERE NOT entity:Chunk AND NOT entity:Document
OPTIONAL MATCH (entity)-[rel]-(related)
WHERE NOT related:Chunk AND NOT related:Document AND related <> entity
RETURN node.text AS chunk_text,
       score,
       collect(DISTINCT entity.name) AS entities,
       collect(DISTINCT type(rel) + ' -> ' + coalesce(related.name, '')) AS entity_relationships
"""

DEFAULT_QUESTIONS = [
    "Who founded Aurora Robotics and what roles do they hold?",
    "Which team develops NovaArm, and what technologies does it use?",
    "Who works on the PathFinder navigation stack?",
]


@dataclass
class AppConfig:
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_database: str | None
    ollama_base_url: str
    ollama_llm_model: str
    ollama_embedding_model: str
    chunk_size: int
    chunk_overlap: int


# ---------------------------------------------------------------------------
# Phase 1: configuration
# ---------------------------------------------------------------------------
def load_configuration() -> AppConfig:
    load_dotenv()
    return AppConfig(
        neo4j_uri=os.environ["NEO4J_URI"],
        neo4j_username=os.environ["NEO4J_USERNAME"],
        neo4j_password=os.environ["NEO4J_PASSWORD"],
        neo4j_database=os.environ.get("NEO4J_DATABASE"),
        ollama_base_url=os.environ["OLLAMA_BASE_URL"],
        ollama_llm_model=os.environ["OLLAMA_LLM_MODEL"],
        ollama_embedding_model=os.environ["OLLAMA_EMBEDDING_MODEL"],
        chunk_size=int(os.environ.get("CHUNK_SIZE")),
        chunk_overlap=int(os.environ.get("CHUNK_OVERLAP")),
    )


# ---------------------------------------------------------------------------
# Phase 2: sample unstructured documents (markdown)
# ---------------------------------------------------------------------------
def ensure_sample_documents() -> list[Path]:
    paths = sorted(DATA_DIR.glob("*.md"))
    if not paths:
        raise FileNotFoundError(
            f"No markdown documents found in {DATA_DIR}. "
            "Add at least one .md file before running the pipeline."
        )
    return paths


# ---------------------------------------------------------------------------
# Phase 3: graph schema (entities, relations, allowed patterns)
# ---------------------------------------------------------------------------
def build_graph_schema() -> dict:
    return {
        "node_types": ["Organization", "Person", "Team", "Product", "Technology"],
        "relationship_types": [
            "FOUNDED",
            "WORKS_AT",
            "MEMBER_OF",
            "PART_OF",
            "DEVELOPS",
            "USES",
        ],
        "patterns": [
            ("Person", "FOUNDED", "Organization"),
            ("Person", "WORKS_AT", "Organization"),
            ("Person", "MEMBER_OF", "Team"),
            ("Team", "PART_OF", "Organization"),
            ("Organization", "DEVELOPS", "Product"),
            ("Team", "DEVELOPS", "Product"),
            ("Product", "USES", "Technology"),
        ],
    }


# ---------------------------------------------------------------------------
# Phase 4: build the knowledge graph (load -> split -> extract -> write)
# ---------------------------------------------------------------------------
async def build_knowledge_graph(
    driver: neo4j.Driver,
    llm: OllamaLLM,
    embedder: OllamaEmbeddings,
    schema: dict,
    document_paths: list[Path],
    neo4j_database: str | None,
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    text_splitter = FixedSizeSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    logger.info("Text splitter: chunk_size=%d chunk_overlap=%d", chunk_size, chunk_overlap)
    kg_pipeline = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        schema=schema,
        text_splitter=text_splitter,
        from_file=True,  # dispatches to MarkdownLoader for .md files
        perform_entity_resolution=True,
        neo4j_database=neo4j_database,
    )
    for path in document_paths:
        logger.info("Building graph from %s", path.name)
        result = await kg_pipeline.run_async(file_path=str(path))
        logger.info("Pipeline result for %s: %s", path.name, result.result)


def reset_graph(driver: neo4j.Driver, neo4j_database: str | None) -> None:
    logger.warning("Resetting graph: deleting all nodes and relationships")
    driver.execute_query("MATCH (n) DETACH DELETE n", database_=neo4j_database)


# ---------------------------------------------------------------------------
# Phase 5: vector index for retrieval over chunk embeddings
# ---------------------------------------------------------------------------
def create_chunk_vector_index(
    driver: neo4j.Driver, embedder: OllamaEmbeddings, neo4j_database: str | None
) -> None:
    dimensions = len(embedder.embed_query("dimension probe"))
    create_vector_index(
        driver,
        name=VECTOR_INDEX_NAME,
        label=CHUNK_NODE_LABEL,
        embedding_property=CHUNK_EMBEDDING_PROPERTY,
        dimensions=dimensions,
        similarity_fn="cosine",
        neo4j_database=neo4j_database,
    )
    logger.info(
        "Vector index '%s' ready on %s.%s (dim=%d)",
        VECTOR_INDEX_NAME,
        CHUNK_NODE_LABEL,
        CHUNK_EMBEDDING_PROPERTY,
        dimensions,
    )


# ---------------------------------------------------------------------------
# Phase 6: retrieval + generation (GraphRAG)
# ---------------------------------------------------------------------------
def answer_questions(
    driver: neo4j.Driver,
    llm: OllamaLLM,
    embedder: OllamaEmbeddings,
    questions: list[str],
    neo4j_database: str | None,
) -> None:
    retriever = VectorCypherRetriever(
        driver,
        index_name=VECTOR_INDEX_NAME,
        retrieval_query=RETRIEVAL_QUERY,
        embedder=embedder,
        neo4j_database=neo4j_database,
    )
    rag = GraphRAG(retriever=retriever, llm=llm)

    for question in questions:
        result = rag.search(
            query_text=question,
            retriever_config={"top_k": 5},
            return_context=True,
        )
        print(f"\nQ: {question}")
        print(f"A: {result.answer}")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset", action="store_true", help="Delete all graph data before building."
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip document ingestion; only (re)build the index and run retrieval.",
    )
    parser.add_argument(
        "--question",
        action="append",
        dest="questions",
        help="Ask a custom question (repeatable). Defaults to a few demo questions.",
    )
    args = parser.parse_args()

    config = load_configuration()

    llm = OllamaLLM(
        model_name=config.ollama_llm_model,
        model_params={"options": {"temperature": 0}},
        host=config.ollama_base_url,
    )
    embedder = OllamaEmbeddings(
        model=config.ollama_embedding_model,
        host=config.ollama_base_url,
    )

    with neo4j.GraphDatabase.driver(
        config.neo4j_uri, auth=(config.neo4j_username, config.neo4j_password)
    ) as driver:
        driver.verify_connectivity()

        if args.reset:
            reset_graph(driver, config.neo4j_database)

        if not args.skip_build:
            document_paths = ensure_sample_documents()
            schema = build_graph_schema()
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
            create_chunk_vector_index(driver, embedder, config.neo4j_database)

        answer_questions(
            driver, llm, embedder, args.questions or DEFAULT_QUESTIONS, config.neo4j_database
        )


if __name__ == "__main__":
    asyncio.run(main())
