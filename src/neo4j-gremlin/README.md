# Neo4j vs Gremlin — Developer Experience Comparison

Local, hands-on comparison of Neo4j (Cypher) vs Gremlin (via Gremlin Server +
TinkerGraph), focused on **developer experience and SDK usage** — not raw
performance. Independent scratch work, isolated from the rest of the
knowledge-layer pipeline (separate containers, separate ports).

## Neo4j
Neo4j is a native property-graph database: nodes, relationships, and both their properties are stored directly as first-class graph structures (not modeled on top of tables or documents), with each node keeping index-free adjacency pointers to its relationships so traversing a connection is a direct pointer lookup rather than a join. It's a single self-contained server (one process, `neo4j:5.23-community` here) with ACID transactions, and everything used in this comparison — Cypher itself, the Bolt protocol, APOC procedures, GDS algorithms — runs inside that one process.

Cypher is Neo4j's query language: declarative, pattern-matching syntax where you draw the shape of the data you want with ASCII art — `(a:Person)-[:FOLLOWS]->(b:Person)` — and the query planner decides how to execute it, much like SQL's `SELECT` describes the result shape rather than the retrieval steps. Cypher is also the basis of openCypher, an open specification other vendors (e.g. AWS Neptune, in one of its two query modes) can implement, though Neo4j's own implementation is the reference one and gets the newest features (GDS calls, subqueries, APOC) first.

**APOC** ("Awesome Procedures On Cypher") is Neo4j's standard utility-procedure library — a plugin, enabled here via the same `NEO4J_PLUGINS` env var as GDS, that adds hundreds of `apoc.*` procedures/functions for things plain Cypher doesn't cover well: JSON/CSV/XML import-export, ad-hoc graph refactoring (merge nodes, redirect relationships), virtual/in-memory graphs, scheduled/triggered procedures, and utility conversions. It's less a query-language feature than a "batteries" pack most real Neo4j deployments install by default. This comparison didn't end up needing any `apoc.*` calls directly (GDS covered the analytics side), but it's worth knowing it's there — Gremlin has no equivalent bundled utility library; anything in that vein means reaching for an external tool or writing it yourself.

## Apache TinkerPop + Gremlin
Apache TinkerPop is an open-source graph computing framework, Gremlin is the functional, imperative query language used to traverse graphs within that framework, and the `tinkerpop/gremlin-server` Docker image is a standalone containerized server that processes those Gremlin queries against an underlying graph database. Think of TinkerPop as the overarching database ecosystem (like JDBC/ODBC in the relational world) and Gremlin as the specific language you write (like SQL) — it's implemented by many different graph databases (JanusGraph, Azure Cosmos DB's Gremlin API, Neptune's other query mode, and Neo4j itself via a community plugin), not tied to any single storage engine.

**Gremlin Server**, specifically, is the piece we're running here: a standalone JVM process that hosts one or more named `TraversalSource`s (our `g`), each bound to an underlying `Graph` instance. In this setup that `Graph` is **TinkerGraph** — TinkerPop's own in-memory reference implementation, good for exactly this kind of local dev/experimentation but with no persistence or clustering story of its own (a real deployment would point the same server config at a persistent, clustered graph like JanusGraph instead). Clients talk to it over a WebSocket (port 8182) using the Gremlin protocol, serialized as GraphSON or GraphBinary — `gremlinpython`'s `DriverRemoteConnection` in `connections.py` is exactly that: a *remote* traversal source, meaning every step in a query we write (`g.V().has(...)`) is actually a request sent over the wire and executed server-side, not a local graph library call.

## Running the experiment

All commands below assume you're in `src/neo4j-gremlin/` and using the
project's existing `.venv` (one directory up). If you're on real Docker
rather than Podman, `docker compose up -d` using `docker-compose.yml` works
the same as `./start.sh`.

**1. Start the databases**
```bash
./start.sh   # starts neo4j-compare (7475/7688) and gremlin-compare (8182)
```

**2. Install dependencies into the project venv**
```bash
../.venv/bin/pip install -r requirements.txt
```

**3. Load the shared dataset into both**
```bash
../.venv/bin/python dataset.py        # sanity-check counts (70/20/10 nodes)
../.venv/bin/python load_neo4j.py     # -> "neo4j: loaded 100 nodes, 423 edges"
../.venv/bin/python load_gremlin.py   # -> "gremlin: loaded 100 nodes, 436 edges"
```
(The edge-count difference is expected — see the "data-model gotcha" in
`COMPARISON.md`.)

**4. Run any query pair to see both backends side by side**
```bash
../.venv/bin/python queries/lookup.py
../.venv/bin/python queries/multi_hop.py
../.venv/bin/python queries/shortest_path.py
../.venv/bin/python queries/aggregation.py
../.venv/bin/python queries/upsert.py
../.venv/bin/python queries/top_n.py
```

**5. Run the analytics comparison**
```bash
../.venv/bin/python analytics/neo4j_analytics.py
../.venv/bin/python analytics/gremlin_analytics.py
```

**6. Explore interactively (optional)**
- Neo4j Browser: `http://localhost:7475` (user `neo4j`, pass `comparepass`) —
  set the connection URL to `bolt://localhost:7688` (not the default 7687,
  since that's the host-mapped port); Safari blocks unencrypted `bolt://`, so
  use Chrome/Firefox
- Gremlin Console (no bundled browser UI like Neo4j — this is the CLI
  equivalent):
  ```bash
  podman run --rm -it -v "$(pwd)/gremlin-remote.yaml:/tmp/remote.yaml" tinkerpop/gremlin-console:3.7
  ```
  then inside the console:
  ```
  :remote connect tinkerpop.server /tmp/remote.yaml
  :remote console
  g.V().limit(10)
  ```
  (`gremlin-remote.yaml` points at `host.containers.internal:8182` — the
  server binds to its own container IP, not `localhost`, so `--network
  container:gremlin-compare` + the default `conf/remote.yaml` doesn't work;
  going through the already-published host port does.)

  `g.V().limit(10)` only prints terse vertex refs (`v[0]`, `v[256]`, ...).
  Vertex/edge labels and properties here are all **lowercase**
  (`person`/`company`/`product`, `follows`/`works_at`/`purchased`) — note
  this differs from Neo4j's capitalized `Person`/`FOLLOWS` below. Some
  useful follow-ups:
  ```
  g.V().limit(10).elementMap()                        // id, label, all properties
  g.V().hasLabel('person').limit(5).elementMap()       // filter by label first
  g.V().has('id', 'p0').elementMap()                   // one specific vertex
  g.V().has('id', 'p0').bothE().elementMap()           // its edges, with properties
  g.V().has('id', 'p0').both().elementMap()            // its neighboring vertices
  ```

  Paired Cypher / Gremlin queries, matching what `queries/*.py` runs against
  the shared dataset:
  ```cypher
  // lookup: people in community 2
  MATCH (p:Person) WHERE p.community = 2 RETURN p.name ORDER BY p.name

  // multi-hop: 2nd-degree follows of p0
  MATCH (a:Person {id: 'p0'})-[:FOLLOWS]->()-[:FOLLOWS]->(b:Person)
  WHERE b.id <> 'p0'
  RETURN DISTINCT b.name ORDER BY b.name

  // shortest path between two people
  MATCH path = shortestPath((a:Person {id: 'p0'})-[:FOLLOWS*]-(b:Person {id: 'p13'}))
  RETURN path

  // aggregation: orders/units per product
  MATCH (:Person)-[r:PURCHASED]->(p:Product)
  RETURN p.name AS product, count(r) AS orders, sum(r.quantity) AS units
  ORDER BY units DESC

  // top-N: most-followed... err, most-following people
  MATCH (p:Person)-[:FOLLOWS]->()
  RETURN p.name, count(*) AS following ORDER BY following DESC LIMIT 5

  // visualize a neighborhood in the graph view
  MATCH (p:Person {id: 'p0'})-[r]-(neighbor) RETURN p, r, neighbor
  ```
  ```
  // lookup: people in community 2
  g.V().hasLabel('person').has('community', 2).values('name').order()

  // multi-hop: 2nd-degree follows of p0
  g.V().has('id', 'p0').out('follows').out('follows')
    .where(__.values('id').is(neq('p0'))).dedup().values('name').order()

  // shortest path between two people (Console has no shortestPath() shortcut like Cypher)
  g.V().has('id', 'p0').repeat(__.both('follows').simplePath())
    .until(__.has('id', 'p13')).limit(1).path().by('name')

  // aggregation: orders/units per product
  g.V().hasLabel('product')
    .project('product', 'orders', 'units')
    .by(__.values('name'))
    .by(__.inE('purchased').count())
    .by(__.inE('purchased').values('quantity').sum())
    .order().by(select('units'), desc)

  // top-N: most-following people
  g.V().hasLabel('person')
    .project('name', 'following')
    .by(__.values('name'))
    .by(__.out('follows').count())
    .order().by(select('following'), desc).limit(5)

  // neighborhood of one person
  g.V().has('id', 'p0').bothE().otherV().path().by(elementMap())
  ```

**7. Stop everything when done**
```bash
./stop.sh
```

## What's compared

| Dimension | Neo4j | Gremlin |
|---|---|---|
| Query language | `queries/lookup.py`, `queries/aggregation.py` | declarative Cypher vs fluent step-chain |
| Traversal & relationships | `queries/multi_hop.py`, `queries/shortest_path.py`, `queries/upsert.py` | ASCII-art patterns vs explicit step traversal; `MERGE` vs `coalesce().fold()` |
| Graph analytics | `analytics/neo4j_analytics.py` | GDS procedures vs no native equivalent (networkx fallback) |
| Tooling / SDKs | Neo4j Browser, official driver, GDS/APOC | Gremlin Console REPL, `gremlinpython` |

Run any module directly, e.g. `python queries/multi_hop.py`, to see both
backends' output side by side.

## Hypotheses

- **H1** — Cypher pattern-matching reads closer to plain language for
  multi-hop/shortest-path queries; Gremlin's step-chain is more verbose but
  easier to slot imperative/conditional logic into mid-traversal.
- **H2** — Cypher's `MERGE` is noticeably shorter and more direct than
  Gremlin's `coalesce().fold()` upsert idiom.
- **H3** — Neo4j's SDK feels more "batteries-included" (typed driver API,
  bundled Browser GUI, GDS, APOC) vs `gremlinpython` feeling lower-level with
  a CLI-only exploration story (Gremlin Console).
- **H4** — Graph analytics is a decisive gap: GDS is native and declarative;
  Gremlin has nothing comparable without reaching for an external library.
- **H5** — For simple single-hop lookups, the two are roughly equivalent in
  code length and clarity — differences only show up once traversal depth or
  analytics enter the picture.

See `COMPARISON.md` for the filled-in findings and final recommendation.
