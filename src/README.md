# Knowledge Layer

Knowledge graph builder and retriever, built on [neo4j-graphrag-python](https://neo4j.com/docs/neo4j-graphrag-python/current/), running entirely on local infrastructure (Ollama + Neo4j via Podman).

## Local Setup

### 1. Neo4j (via Podman)

Run a local Neo4j instance:

```bash
podman run -d \
  --name neo4j-kg \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/my_password \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v neo4j_data:/data \
  -v neo4j_logs:/logs \
  neo4j:5.23-community
```

Notes:
- Use Neo4j **5.13+** — native vector index support (required by the retriever) needs it. `5.23-community` above satisfies this.
- Replace `my_password` with a real password (8+ chars) and keep it for your `.env`.
- APOC isn't strictly required for the KG builder pipeline but is commonly needed for graph utility procedures.
- Named volumes (`neo4j_data`, `neo4j_logs`) persist data across container restarts.

Verify it's up:

```bash
podman logs -f neo4j-kg   # wait for "Started."
```

Check the browser UI at `http://localhost:7474` (login `neo4j` / your password), or verify bolt connectivity directly:

```bash
podman exec neo4j-kg cypher-shell -u neo4j -p my_password "RETURN 1;"
```

### 2. Ollama (via Podman)

> Note: on macOS, containers can't access Metal/GPU, so Ollama in Podman runs CPU-only and will be slower than a native install (`brew install ollama`). Use whichever fits your setup — the steps below assume Podman for consistency with Neo4j.
>
> **Memory:** the default Podman machine on macOS is allocated only 2GB RAM, which is not enough to load a 7B model (`qwen2.5:7b-instruct` needs ~4-5GB). If you hit an error like `ggml_aligned_malloc: insufficient memory` or `llama-server process has terminated`, raise the VM's memory:
> ```bash
> podman machine stop
> podman machine set --memory 8192   # 8GB; adjust to your host's available RAM
> podman machine start
> ```

```bash
podman run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  docker.io/ollama/ollama:latest
```

Verify it's up:

```bash
podman logs -f ollama   # wait for "Listening on"
curl http://localhost:11434/api/tags
```

Pull the models used by this project:

```bash
podman exec -it ollama ollama pull qwen2.5:7b-instruct   # LLM used for entity/relation extraction
podman exec -it ollama ollama pull nomic-embed-text      # embedding model used for retrieval
```

Confirm they're available:

```bash
podman exec -it ollama ollama list
```

Model choices:
- **`qwen2.5:7b-instruct`** — LLM for the KG builder pipeline. Strong structured/JSON output, good speed on modest hardware, reliable for schema-constrained entity/relation extraction.
  - Alternative: `llama3.1:8b-instruct-q4_0` (slightly less reliable JSON adherence).
- **`nomic-embed-text`** — 768-dim embedding model for the vector retriever. Fast and good quality for RAG.
  - Alternative: `mxbai-embed-large` for higher quality at more compute cost.

### 3. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Environment variables

Create a `.env` file (see `.env.example`) with your Neo4j credentials and Ollama endpoint:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=my_password
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=qwen2.5:7b-instruct
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
CHUNK_SIZE=4000
CHUNK_OVERLAP=200
```

`CHUNK_SIZE`/`CHUNK_OVERLAP` control the `FixedSizeSplitter` used during the build phase (characters per chunk, and how many characters of overlap between consecutive chunks). Both are optional and default to `4000`/`200` (the `neo4j-graphrag` library defaults) if omitted.

## Stopping and resuming the local servers

Both containers keep their data in named volumes, so stopping them is safe — nothing is lost, and starting them again picks up right where you left off.

**Stop both after you're done working:**

```bash
podman stop neo4j-kg ollama
```

**Resume both at the start of a session:**

```bash
podman start neo4j-kg ollama
```

Check they're running:

```bash
podman ps --filter name=neo4j-kg --filter name=ollama
```

If you ever want to remove them entirely (e.g. to rebuild from scratch) — this does **not** delete the named volumes (`neo4j_data`, `neo4j_logs`, `ollama_data`), so pulled models and graph data survive:

```bash
podman rm -f neo4j-kg ollama
```

## Running the pipeline

With Neo4j and Ollama up (see above) and the Python environment set up, run the pipeline from this directory:

```bash
python graph_rag_pipeline.py
```

This runs all phases in order: loads the sample markdown documents in `data/docs/`, builds the knowledge graph (entity/relation extraction via `qwen2.5:7b-instruct`, written to Neo4j), creates a vector index over chunk embeddings, then asks a few demo questions and prints the GraphRAG answers.

Retrieval uses `VectorCypherRetriever`, not the plain `VectorRetriever`: after the vector index finds the most similar chunks, a Cypher `retrieval_query` walks `(entity)-[:FROM_CHUNK]->(chunk)` to the entities extracted from each matched chunk, then one hop further to their neighbors in the graph. So the LLM gets both the chunk text and the surrounding entity graph (people, teams, products, technologies), not just raw chunk text.

The graph schema itself — what node types and relationship types the extractor is allowed to find, and which `(source, relationship, target)` patterns are valid — is not hardcoded in the script. It's loaded from `ontology.ttl`, a plain OWL/RDFS ontology in Turtle syntax: `owl:Class` declarations become node types, and `owl:ObjectProperty` declarations become relationship types, with each property's `rdfs:domain`/`rdfs:range` becoming an allowed pattern (a property with multiple domains, like `DEVELOPS`, produces one pattern per domain). To extend the schema — say, add a new entity type or relationship — edit `ontology.ttl` and re-run with `--reset`; no code changes needed.

Useful flags:

```bash
python graph_rag_pipeline.py --reset          # wipe the graph before rebuilding
python graph_rag_pipeline.py --skip-build      # skip ingestion, just (re)index + retrieve against the existing graph
python graph_rag_pipeline.py --question "Who leads the Manipulation Team?"   # ask your own question (repeatable)
```

Chunking is controlled via `CHUNK_SIZE`/`CHUNK_OVERLAP` in `.env` (see above) — not command-line flags. Change them there and re-run with `--reset` to rebuild with a different chunk size.

A full build over the 3 sample documents takes a few minutes on CPU-only local models — `--skip-build` is useful for iterating on retrieval/prompting without re-running extraction.

## Alternate entry point: `kg_pipeline_cli.py`

`kg_pipeline_cli.py` is a parallel, subcommand-style entry point over the same pipeline logic (it imports directly from `graph_rag_pipeline.py` rather than duplicating it), inspired by the CLI shape of the sibling `Unstructured-Data-to-graph` project's `src/main.py`. Where `graph_rag_pipeline.py` is one flag-driven script that builds and queries in a single run, this one splits those into discrete commands:

```bash
python kg_pipeline_cli.py ingest data/docs             # build the graph from a docs directory
python kg_pipeline_cli.py ingest data/docs --reset     # wipe the graph first
python kg_pipeline_cli.py chat                          # interactive Q&A REPL
```

`ingest` prints a diff report after building — documents/entities/relationships added or removed compared to the graph's state right before the run (including what a `--reset` wiped). It only tracks additions/removals, not in-place content changes to an existing document, since that would need a persisted content hash per document.

`chat` is an interactive REPL (`exit`/`quit` to leave) instead of a fixed batch of demo questions, and prints the source entities and graph relationships behind each answer as citations. It does not stream tokens — `GraphRAG.search` is a single blocking call.

Unlike the sibling project, this script skips the candidate-graph/ontology-approval/publish-gating workflow entirely: `ingest` writes straight to the graph, exactly like `graph_rag_pipeline.py` does.

### Trying it out

1. **Build a clean baseline** from the original sample documents:
   ```bash
   python kg_pipeline_cli.py ingest data/docs --reset
   ```
   The diff report should show `data/docs/*.md` added and nothing removed (or, on a fresh Neo4j instance, everything added).

2. **Add new data without disturbing what's already in the graph** — put one or more new markdown files in a separate directory (not `data/docs/`, so you don't touch the originals) and `ingest` that directory **without** `--reset`:
   ```bash
   mkdir -p data/docs_extra
   # write a new .md file into data/docs_extra/ introducing entities/relationships
   # not already present elsewhere in the corpus, e.g. a new team, person, or product
   python kg_pipeline_cli.py ingest data/docs_extra
   ```
   Because `ingest` only ever reads the directory you pass it, this merges the new content into the existing graph instead of replacing it. The diff report should show only additions (the new document, its new entities, its new relationships) with `0` removed. Confirm the original data survived by checking directly in Neo4j Browser (see below) that entities from `data/docs/` are still there.

3. **Ask a question that spans both the original and the newly added data**:
   ```bash
   python kg_pipeline_cli.py chat
   ```
   At the `You:` prompt, ask something that requires connecting an original entity to a newly added one (e.g. relating a new product to an existing one), confirm the answer plus its citations block look right, then type `exit`.

## Viewing the graph in Neo4j Browser

1. Open `http://localhost:7474` in a browser and log in (`neo4j` / your password from the `.env`).
2. Run a Cypher query to see everything the pipeline built:
   ```cypher
   MATCH (n) RETURN n LIMIT 300
   ```
3. A few more targeted views:
   ```cypher
   // Just the extracted entity graph (people, orgs, teams, products, technologies)
   MATCH (n) WHERE NOT n:Chunk AND NOT n:Document AND NOT n:__KGBuilder__ RETURN n

   // The lexical graph: documents and their chunks
   MATCH (d:Document)-[:FROM_DOCUMENT|PART_OF_DOCUMENT|HAS_CHUNK*0..1]-(c:Chunk) RETURN d, c

   // How a specific person connects to the rest of the graph
   MATCH (p:Person {name: "Maya Chen"})-[r]-(n) RETURN p, r, n
   ```
4. Click any node in the results to expand its relationships visually, or double-click to expand connected nodes directly in the graph view.

## Project layout

- `data/docs/` — sample unstructured markdown documents used as the source corpus.
- `ontology.ttl` — the graph schema (node types, relationship types, allowed patterns), as an OWL/RDFS ontology in Turtle syntax.
- `graph_rag_pipeline.py` — the KG builder + retriever pipeline (single script, phased).
- `kg_pipeline_cli.py` — alternate `ingest`/`chat` subcommand entry point over the same pipeline logic (see above).
- `requirements.txt` — Python dependencies.
