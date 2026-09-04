# GraphRAG

Ref: https://neo4j.com/blog/genai/what-is-graphrag/

GraphRAG is a powerful retrieval mechanism that improves GenAI applications by taking advantage of the rich context in graph data structures.

RAG systems rely solely on semantic search in vector databases to retrieve and rank sets of isolated text fragments. While this approach can surface some relevant information, it fails to capture the context connecting these pieces. For this reason, basic RAG systems are ill-equipped to answer complex, multi-hop questions.

This is where GraphRAG comes in. It uses tabknowledge graphs to represent and connect information to capture not only more data points but also their relationships. Thus, graph-based retrievers can provide more accurate and relevant results by uncovering hidden connections that aren’t often obvious but are crucial for correlating information.

A knowledge graph model is especially suitable for representing structured and unstructured data with connected elements. Unlike traditional databases, they don’t require a rigid schema but are more flexible in the data model. The graph model allows efficient storage, management, querying, and processing of the richness of real-world information.

A GraphRAG retrieval can find starting points in this network of data via vector, fulltext, spatial, or other searches and then follow relevant relationships to gather additional information to satisfy the user queries. The context of the user and task is considered to increase relevance. All captured nodes, relationships and their attributes can be filtered and ranked before being returned as context in the augmentation phase.

![GraphRAG diagram](https://dist.neo4j.com/wp-content/uploads/20241205001949/graphrag-diagram.png)

## How GraphRAG improves retrieval
This approach offers several advantages over vector-only RAG systems:
1. By navigating the graph structure and following relevant relationships, GraphRAG can retrieve information that may not be directly mentioned in the initial set of retrieved chunks, providing a more comprehensive and contextually relevant response.
2. The ability to filter and rank the retrieved information based on the user’s context and task allows GraphRAG to prioritize the most pertinent information, improving the overall quality of the generated response.
3. GraphRAG enables better explainability by capturing the relationships between the retrieved information, making it easier to trace the sources and reasoning behind the generated response.
4. By using the knowledge graph’s ability to integrate structured and unstructured data, as well as computed signals, GraphRAG can provide more informed and nuanced responses that draw from a wider range of information sources.

## Types of GraphRAG retrievers
The actual graph retrieval depends on the use case and domain. Different types of retrievers can be combined, and their results ranked, combined, or sequenced. In an agentic setup, retrievers can become tools that the LLM selects and runs iteratively, passing parameters and results until the necessary information to answer the question is collected.
Examples of GraphRAG retriever types include:
Vector (Embedding), Fulltext, Spatial, or other Search Indexes: Using index searches with information from the user question to determine starting points in the graph for further exploration.
Neighborhood Traversal: Access direct or indirect neighbors of a node to put a piece of information into context.
Path Traversals: Find paths between starting entities, expand relationships to their neighborhood, and retrieve additional related documents, claims, and other entities.
Global Queries: Using pre-computed, cross-topic summarization and other global representations of insights to answer general questions (see Microsoft’s GraphRAG with Query Focused Summarization).
opens in new tabQuery Templates: Use case-specific queries for categories of questions are provided by a domain expert, can have the same starting points but explore different sub-graphs, and can be selected by categorizing questions.
opens in new tabDynamic Cypher Generation (opens in new tabText2Cypher): A (fine-tuned) LLM generates a Cypher query from the user question and the graph schema description to answer specific and structural questions.
Agentic Traversal: Using different retrievers, an LLM selects and executes them in a planned sequence to collect all information to answer the question.
Graph Embedding Retrievers: Using embeddings to represent the “essence” of a node’s neighborhood and allow fuzzy topological search by matching candidate embeddings.

## Knowledge graph construction

For GraphRAG to work well, we need to ensure that our data has a shape that accurately represents the highly relevant, connected pieces of information. To create this knowledge graph, we need to follow two steps, which can be repeated for refinement:
Model the relevant nodes and relationships to represent our domain data.
Import, create, or compute the graph structures to fit this graph model.

![Knowledge graph construction](https://dist.neo4j.com/wp-content/uploads/20241204071429/build-knowledge-graph.png)

We can combine different sources of data:
1. Import existing structured data from databases, files or APIs.
Turn unstructured data (text, audio, video) into a graph representation of document structures/hierarchies and add vector embeddings and full-text indexes for chunks.
2. Construct or connect structured entities (with optional embeddings) and their relationships from textual information.
3. Enhance existing graphs with additional computation or algorithms, such as topic-clustering summaries (like in Microsoft Query Focused Summarization), similarity relationships, and personalized page rank (PPR) scores.
4. These graph models and sources are also described in more detail in the GraphRAG pattern catalog.

## A GraphRAG example with Neo4j
A frequent use case for GraphRAG is analyzing research information in more detail than just “chatting with your PDF.” In a vector-only semantic search approach, the data returned from the retrievers are just scored chunks of text with little or no information on how they relate to concepts from the domain or each other.

In contrast, a GraphRAG approach allows us to extract entities such as Person, Organization, Article, Paper, BiologicalProcess, Condition, Disease, Drug, Gene, Expression, Exposure, and Pathway that appear in our documents and create a rich network of information.

To demonstrate this, let’s walk through an example of constructing a knowledge graph using the open source neo4j-graphrag package. You can also use LangChain, LlamaIndex, or other opens in new tabintegrations.

![GraphRAG with Neo4j](https://dist.neo4j.com/wp-content/uploads/20241015075828/simplekgpipeline-1.png)

## Why not plain vector RAG

```
 Vector RAG                        GraphRAG
 ┌────────────┐                   ┌────────────┐
 │ chunk 1    │  similarity only  │  entity ── relation ── entity │
 │ chunk 2    │  no connections   │     │                  │      │
 │ chunk 3    │  between chunks   │  relation           relation  │
 └────────────┘                   │     │                  │      │
                                   │  entity ── relation ── entity │
                                   └────────────────────────────────┘
```
Vector RAG retrieves texts that *look* similar; GraphRAG retrieves entities that are *actually connected* — better for multi-hop, "how are X and Y related" style questions.

## Phase 1 — Build the graph from a source

```
┌───────────┐   ┌────────────┐   ┌───────────────┐   ┌────────────┐   ┌──────────────┐
│  Source   │──▶│  Splitter  │──▶│  LLM extractor │──▶│  Embedder  │──▶│  Knowledge   │
│ (docs,    │   │ (chunk     │   │ (entities +    │   │ (vectors   │   │  Graph (DB)  │
│ APIs, DBs,│   │  large     │   │  relationships, │   │  per chunk/│   │  e.g. Neo4j  │
│  audio)   │   │  text)     │   │  per schema)    │   │  entity)   │   │              │
└───────────┘   └────────────┘   └───────────────┘   └────────────┘   └──────────────┘
```

1. **Model the schema first** — decide node labels (`Person`, `Drug`, `Organization`, …) and relationship types before extraction. A defined schema keeps LLM extraction consistent.
2. **Ingest & split** — pull in structured data (DB/API tables → nodes/edges directly) and unstructured data (text/audio/video); split long text into manageable chunks.
3. **Extract entities & relationships** — an LLM reads each chunk against the schema and emits `(entity)-[relationship]->(entity)` triples.
4. **Embed** — generate vector embeddings for chunks and/or entities so the graph is also vector-searchable (hybrid retrieval).
5. **Load into the graph DB** — write nodes, relationships, and embeddings (e.g. via Neo4j's `SimpleKGPipeline`).
6. **Enrich (optional)** — run graph algorithms (community detection/clustering, similarity scoring) and store results back as node properties for cheap reuse at query time.

## Phase 2 — Query the graph at retrieval time

```
 User question
      │
      ▼
┌─────────────┐    entry points     ┌────────────────┐   1-2 hop     ┌──────────────┐
│ Index search │ ───(vector/full-  ─▶│ Seed node(s)   │──expansion──▶│ Neighborhood  │
│ (vector /    │     text/spatial)   │ in the graph   │  along edges  │ subgraph      │
│  fulltext)   │                    └────────────────┘               └──────────────┘
                                                                             │
                                                                             ▼
                                                                    ┌──────────────┐
                                                                    │ Rank & filter │
                                                                    │ nodes/edges   │
                                                                    └──────────────┘
                                                                             │
                                                                             ▼
                                                                    ┌──────────────┐
                                                                    │ LLM answer    │
                                                                    │ (augmented    │
                                                                    │  context)     │
                                                                    └──────────────┘
```

1. **Find entry points** — use vector/fulltext/spatial index search over the question to locate the most relevant seed node(s) in the graph.
2. **Traverse outward** — expand 1–2 hops from the seed nodes, following relationships to pull in first- and second-degree neighbors (not just the directly matched chunk).
3. **Rank & filter** — score retrieved nodes/relationships/attributes by relevance and prune before passing to the LLM (avoid context bloat).
4. **Augment & generate** — inject the ranked subgraph (as text/triples) into the LLM prompt alongside the question; the LLM generates the final answer.

### Retriever strategies (mix as needed)
- Vector / fulltext / spatial index search
- Neighborhood traversal (N-hop expansion)
- Path traversal between two known entities
- Pre-computed global queries (e.g. community summaries)
- Domain-specific query templates
- Dynamic Cypher generation from natural language (text-to-query)
- Agentic selection — an agent picks which retriever(s) to use per question

## End-to-end summary

```
Source data ─▶ Schema design ─▶ Extraction (LLM) ─▶ Graph DB ─▶ [query time] ─▶
Index search ─▶ Graph traversal ─▶ Rank/filter ─▶ LLM + context ─▶ Answer
```
