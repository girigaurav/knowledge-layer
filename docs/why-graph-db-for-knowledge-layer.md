# Why a Graph Database for the Knowledge Layer

Our knowledge layer models real-world entities and the relationships between them — exactly the shape a graph database is built for. Relational and document stores treat relationships as a runtime cost: every traversal means a join or a lookup, and that cost grows with data volume and query depth. A graph database (Neo4j/Gremlin) stores relationships as first-class data, so traversing connected entities — regardless of how many hops away — stays fast and predictable. This is critical for our use case: answering "how is X connected to Y" style questions, powering search and discovery, and grounding GenAI question-answering with accurate, contextual retrieval instead of brittle keyword or embedding-only matches.

Beyond performance, graphs let us layer **organizing principles** (schemas, taxonomies, ontologies) directly on top of the data without redesigning the underlying model — critical as our domain vocabulary and use cases evolve. This flexibility means we can start narrow (a specific use case) and expand scope over time without a costly migration, while keeping data and its context together in one queryable structure. For a knowledge layer meant to surface insight and support reasoning over connected information, a graph database isn't just a storage choice — it's the model that matches the problem.

## Features that help us build and maintain it

- **Schema-optional / evolving schema** — new entity and relationship types can be added without migrations, so the model can grow alongside our ontology instead of being redesigned each time.
- **Native query languages (Cypher, Gremlin)** — pattern-matching queries express multi-hop relationships in a few lines, making both ad-hoc exploration and pipeline queries easy to write and read.
- **Constraints & indexes** — uniqueness constraints, property indexes, and (where supported) schema validation keep entity/relationship data consistent as multiple pipelines write to the graph.
- **Built-in graph algorithms** (centrality, community detection, shortest path, similarity) — usable directly for enrichment, deduplication, and surfacing related entities without exporting data to a separate analytics engine.
- **ACID transactions** — safe concurrent writes as ingestion pipelines and manual edits update the graph at the same time.
- **Visualization & tooling** — native browsers/explorers make it far easier to inspect, debug, and validate the graph structure than querying rows in a table.
