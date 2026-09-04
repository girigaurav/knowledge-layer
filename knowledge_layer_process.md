# Knowledge Layer — Process Document (PM Overview)

**Purpose of this doc:** a plain-language walkthrough of the work required to (1) build our ontology-based knowledge graph, and (2) use it to power a "GraphRAG" question-answering pattern — plus the tools we'd use for each.

---

## The big picture

Think of it as three layers, built in order:

1. **Ontology** — a map of the business: the concepts we care about (Customer, Order, Refund...), how they relate, and the rules that govern them (e.g. "an order can only be refunded once").
2. **Knowledge Graph** — the actual data, loaded in so it matches that map.
3. **GraphRAG** — the retrieval pattern that lets an AI assistant use that map + data to answer questions accurately, instead of guessing from raw text alone.

Everything below is the work required to get from nothing to a working version of all three.


## Part 1: Building the Ontology-Based Knowledge Graph

| Step | What it means | Work required |
|---|---|---|
| **1. Pick a starting scope** | Don't try to map the whole business at once. Pick one process or product area to start (e.g. one support workflow). | Business + tech team agree on a pilot scope. |
| **2. Define the business map** | Write down, in plain terms, the key concepts and how they connect — e.g. *Customer places an Order, an Order contains Products, an Order can be Refunded.* | Workshops with domain experts to sketch this out. Can be done two ways at once: experts define it top-down, **and** we scan existing documents/tickets to see what terms and relationships actually show up in practice (bottom-up). Reconcile the two. |
| **3. Reuse existing standards where possible** | Don't invent vocabulary from scratch if a recognized standard already covers it (e.g. FIBO for finance, Schema.org for general business concepts). | Decision needed: do we adopt a standard as-is, or a customized version? (Open question — see below.) |
| **4. Map business terms to real systems** | Connect the business map to where the data actually lives — e.g. "Customer's first name" lives in the Oracle database, column `F_NAME`. | Data/engineering team documents source systems, tables, and columns for each business concept. |
| **5. Add the rules** | Turn "an order can only be refunded once" from a sentence into a rule the system actually enforces. | This is where the ontology gets formalized (technical step, using RDF/OWL standards — see tools section). Prevents bad data and bad AI decisions later. |
| **6. Decide the shape of the graph** | Depending on the use case, we may need just structured business data, or also documents split into searchable chunks, or clusters of related topics summarized by AI. | Decision needed: which "shape" fits our use case? (Open question — see below.) |
| **7. Load the data in** | Pull in data from databases, documents, tickets, etc., extract the entities/relationships, and load everything into the graph database. | Engineering build — ingestion pipeline. If we're using Databricks, this fits the existing raw → cleaned → business-ready pattern already in use. |
| **8. Check and version it** | Validate that new data doesn't break the rules from Step 5, and keep track of changes to the map over time as the business evolves. | Ongoing governance process, not a one-time task. |

**Bottom line:** Steps 1–4 are mostly workshops and documentation (business-led). Steps 5–8 are technical build work, but they depend entirely on Steps 1–4 being right first.

---

## Part 2: Building the Ontology-Based GraphRAG Pattern

Once the knowledge graph exists, this is how we make it answer questions reliably.

**Why not just use plain AI search (vector search)?** Plain AI search finds text that *sounds* similar to the question, but doesn't know how facts *connect*. It struggles with questions like "how are X and Y related" or anything needing multiple linked facts. GraphRAG fixes this by using our graph's actual relationships, not just word similarity.

### How it's built (one-time setup)

1. Break source documents/tickets into smaller pieces.
2. Use AI to pull out entities and relationships from each piece, matching them to our ontology (Part 1).
3. Create AI "fingerprints" (embeddings) of the same text, for similarity search.
4. Load all of this into the graph database.

### How it answers a question (every time a user asks)

1. **Find a starting point** — search finds the most relevant record for the question (e.g. the right support ticket).
2. **Follow the connections** — the graph pulls in directly related facts (e.g. similar tickets, the specific fields needed).
3. **Filter to what matters** — trim down to the most relevant pieces so the AI isn't overwhelmed.
4. **Generate the answer** — the AI writes the final answer using that curated, connected context.

**Example:** A user asks *"how do I reproduce the CSV upload error?"* → search finds the matching ticket → the graph pulls in that ticket's fields and similar past tickets → the AI answers with the actual reproduction steps, instead of a generic guess.

### Making it safer for AI agents that take action (not just answer questions)

If we go further and let an AI agent actually *do things* (not just answer questions), the ontology's rules from Part 1, Step 5 double as a safety check: before and after every action, the system checks the request and the result against the rules (e.g. "this would be a second refund on the same order — reject it"). This catches mistakes before they cause real damage, rather than relying on the AI to get it right on its own every time.

Every time this runs, we should also record what happened (which path was used, whether it worked) — over time this becomes a memory layer that helps the system get better at choosing the right path, not just a valid one.

---

## Tools & Frameworks We'd Use

| Purpose | Tool | Why |
|---|---|---|
| Graph database (stores the knowledge graph) | **Neo4j** | Most mature tooling for this exact pattern; has built-in support for both the graph and the AI search index. |
| Ontology authoring (defining the business map + rules) | **Protégé** (visual tool) | Lets domain experts view/edit the map without writing code. |
| Building the pipeline that extracts data into the graph | **LangChain**, **LlamaIndex**, or Neo4j's own toolkit (`neo4j-graphrag`) | All three can turn raw documents into a knowledge graph automatically using AI. Neo4j's own toolkit is the most tightly integrated if we commit to Neo4j. |
| Checking AI actions are safe before they run | **Pydantic** | Validates that an AI's request is well-formed before it's allowed to execute. |
| Governed data pipeline (if using Databricks) | **Databricks + Unity Catalog** | Reuses our existing raw → cleaned → business-ready data pattern and access controls. |

**Simplest starting stack:** Neo4j (database) + Neo4j's own toolkit (pipeline) + Protégé (for business experts to define the map) + Databricks (if source data already lives there).

---

## Decisions We Still Need From the Team

1. **How do we build the ontology?** Top-down (experts define it), bottom-up (mine it from existing docs), or both together (recommended)?
2. **Do we adopt an industry standard** (e.g. FIBO) as-is, or customize it for us?
3. **What shape of graph do we actually need** for this use case? (Just business data, or also document search, or also AI-generated topic summaries?)
4. **Which framework** — Neo4j's own toolkit, LangChain, or LlamaIndex?
5. **Confirm Neo4j** as the graph database, or note if there's a reason to use something else.

---

## Suggested Next Step

Run a small pilot on **one** business process end-to-end (map it → load it → ask it questions) before committing to a bigger rollout. This proves the pattern works and surfaces real issues cheaply, before scaling up.
