# Findings — Neo4j (Cypher) vs Gremlin

Ran against the shared 100-node synthetic dataset (`dataset.py`) loaded
identically into both (`load_neo4j.py` / `load_gremlin.py`), using
`neo4j-compare` (Neo4j 5.23 + APOC + GDS) and `gremlin-compare` (Gremlin
Server 3.7 + TinkerGraph) via Podman.

## Query language & aggregation

| Query | Cypher | Gremlin | Note |
|---|---|---|---|
| `lookup.py` | 3-line `WHERE` + `RETURN` | 4-step fluent chain | About equal — H5 confirmed for simple filters. Identical results. |
| `aggregation.py` | `MATCH` + `count()`/`sum()` + `ORDER BY`, 1 statement | `project().by().by().by()` chain, one `.by()` per output field | Comparable length, but Gremlin requires an explicit `.by()` per projected field even for a single MATCH-shaped query — Cypher's `RETURN a, count(b), sum(c)` reads more like the question being asked. |

## Traversal & relationships

| Query | Cypher | Gremlin | Note |
|---|---|---|---|
| `multi_hop.py` | 1 ASCII-art pattern line + 1 `WHERE` clause | `.out().out().where(__.values("id").is_(P.neq(...)))` | Gremlin needs an extra nested traversal (`P.neq`) just to exclude self by property; Cypher's `b.id <> $id` is direct. Same result set on both. |
| `shortest_path.py` | Built-in `shortestPath()` function, 1 line | Manual `repeat().until().limit(1).path()` BFS | TinkerPop *does* have a `shortestPath()` step, but its `.with_(ShortestPath.target, ...)` config-object API is awkward enough that hand-rolled BFS is the more common idiom — confirmed while researching this. Cypher's version is dramatically less code and no algorithmic knowledge required. |
| `upsert.py` | `MERGE (p:Person {id: $id}) SET ...`, 1 line | `fold().coalesce(unfold(), addV()...)` idiom | Textbook case: Cypher's `MERGE` is a single declarative primitive; Gremlin's fold/coalesce/unfold upsert is a well-known idiom precisely *because* it's non-obvious — most Gremlin newcomers have to learn it from a blog post. |
| `top_n.py` | `MATCH` + `ORDER BY` + `LIMIT`, 3 lines | `project().by().by().order().by().limit()`, similar length | Roughly equal once you already know the `project()` pattern. |

**Data-model gotcha found while loading**: Cypher's `MERGE (a)-[r:PURCHASED]->(b)` treats repeat purchases between the same person/product as *one* relationship (last write wins on `r.quantity`), collapsing 436 raw edges to 423. Gremlin's `addE()` has no such implicit identity semantics — it created all 436. Neither is "wrong"; it's a reminder that `MERGE` on a relationship pattern is itself a modeling decision (repeat interactions usually want their own event node in *either* system), and it silently changed the aggregation totals between the two backends even though both queries are correct.

## Graph analytics

| Algorithm | Neo4j (GDS) | Gremlin |
|---|---|---|
| Degree centrality | `CALL gds.degree.stream(...)`, native, 1 line | Native traversal step (`both_e().count()`), no extra tooling |
| PageRank | `CALL gds.pageRank.stream(...)`, native, 1 line | **No native step.** Exported the subgraph and ran `networkx.pagerank()` — a whole extra library + an explicit export step just to get a number Neo4j gives you for free |
| Community detection (Louvain) | `CALL gds.louvain.stream(...)`, native, 1 line | **No native step.** Same networkx export, `greedy_modularity_communities()` (a different algorithm entirely — Gremlin/TinkerPop doesn't even have Louvain available OLTP-side) |

Both PageRank rankings actually agreed closely on the top nodes (Person50,
Person15, Person14, Person68 in nearly the same order) — so the *results*
were fine. The gap is entirely about developer experience: GDS is "ask the
database," Gremlin here is "export the graph and bring your own algorithm
library, which may not even be the same algorithm."

## Tooling / SDKs (observed while building this)

- **Neo4j**: official `neo4j` Python driver's `driver.execute_query(...)` is a one-call, typed-record convenience API — no manual session/transaction boilerplate needed for any query here. Neo4j Browser is bundled and reachable at `http://localhost:7475` with zero extra setup. Adding GDS/APOC was a single `NEO4J_PLUGINS` env var on the official Docker image.
- **Gremlin**: `gremlinpython` requires manually opening (`DriverRemoteConnection`) and closing a connection per script — no bundled connection-pooling convenience layer comparable to `execute_query`. It does offer Pythonic snake_case step aliases (`add_v`, `has_label`, `sum_`) alongside the historical Java-style camelCase, which helps readability once you know the mapping exists. There's no bundled web UI; exploration happens via the Gremlin Console (CLI REPL) or by writing scripts like these — a materially higher floor to "poke at the graph interactively."

## Hypothesis verdicts

| # | Hypothesis | Verdict | Why |
|---|---|---|---|
| H1 | Cypher reads closer to plain language for multi-hop/shortest-path | **Supported** | `shortestPath()` vs manual BFS and the pattern-match vs step-chain examples above are the clearest evidence. |
| H2 | `MERGE` beats `coalesce().fold()` for upserts | **Supported** | 1 line vs a named idiom that has to be learned separately. |
| H3 | Neo4j SDK is more batteries-included | **Supported** | `execute_query`, bundled Browser, one-env-var plugin install vs manual connection handling and CLI-only exploration. |
| H4 | Analytics is a decisive native-vs-bolted-on gap | **Supported, strongly** | Degree centrality is native on both; PageRank/community detection are native only in Neo4j and require an entirely separate library (with a different algorithm) in Gremlin. |
| H5 | Simple single-hop lookups are roughly equivalent | **Supported** | `lookup.py` and `top_n.py` came out comparable in length and clarity on both sides. |

## Recommendation

For this team's use case — a home-grown knowledge-graph layer where
developers will be hand-writing and maintaining traversal/analytics queries
day to day (per `docs/questions.md`'s Technology section) — **Neo4j/Cypher
is the stronger developer-experience choice**. The gap isn't close on three
of the five dimensions tested (upserts, shortest-path, analytics), it's a
wash on the other two, and Neo4j never loses. The one place Gremlin's
model earns its keep is portability — it's the query language Azure Cosmos
DB's Gremlin API speaks, so if the Azure-managed, multi-model route from
`docs/questions.md` becomes the actual direction (Cosmos over a home-grown
Neo4j deployment), that's a cost worth re-weighing against the DX gap found
here, not a reason to dismiss it.
