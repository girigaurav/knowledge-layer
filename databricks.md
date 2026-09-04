# Databricks

## Medallion Architecture

A layered data design pattern that incrementally improves data quality as it moves through stages: **Bronze → Silver → Gold**.

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│    BRONZE    │      │    SILVER    │      │     GOLD     │
│  raw / as-is │ ───▶ │  cleaned /   │ ───▶ │  aggregated  │
│              │      │  validated / │      │  business-   │
│              │      │  conformed   │      │  level views │
└──────────────┘      └──────────────┘      └──────────────┘
      ▲                                            │
      │                                            ▼
 source systems                          BI / ML / dashboards
 (files, APIs, CDC)
```

- **Bronze** — raw ingestion, append-only, source schema preserved (audit trail).
- **Silver** — deduplicated, filtered, joined; enforced schema; queryable by data teams.
- **Gold** — aggregated, denormalized, consumption-ready (dashboards, ML features, reports).

Each layer is typically a Delta table, giving ACID transactions, schema enforcement, and time travel at every stage.

## Unity Catalog

Centralized governance layer for data + AI assets across all workspaces in an account — one metastore, consistent permissions, lineage, and auditing everywhere.

```
                     Account
                        │
                 Unity Catalog Metastore
                        │
        ┌───────────────┼───────────────┐
        │               │               │
     catalog          catalog         catalog
        │
   ┌────┴────┐
   │         │
 schema    schema
   │
 ┌─┴─────────────┐
 │        │      │
table   view   volume / function / model
```

- **Metastore** — top-level container, one per region/account, shared across workspaces.
- **Catalog** → **Schema** → **Table/View/Volume/Function/Model** — 3-level namespace: `catalog.schema.table`.
- Central features: access control (GRANT/REVOKE), data lineage, audit logs, Delta Sharing, tagging/discovery via Catalog Explorer.

## Workspaces

A workspace is the Databricks environment where users run notebooks, jobs, clusters, and ML experiments — the "workbench," separate from where data is governed.

```
        Unity Catalog Metastore  (governance, shared)
              │            │
      ┌───────┘            └───────┐
      ▼                            ▼
 ┌───────────┐               ┌───────────┐
 │Workspace A│               │Workspace B│
 │ (e.g. dev)│               │ (e.g.prod)│
 │           │               │           │
 │ notebooks │               │ notebooks │
 │ clusters  │               │ clusters  │
 │ jobs/ML   │               │ jobs/ML   │
 └───────────┘               └───────────┘
```

- Multiple workspaces (dev/staging/prod, per-team, per-region) can attach to the **same** Unity Catalog metastore, so data governance stays consistent while compute/workspace boundaries stay separate.
- Workspaces host the compute (clusters/SQL warehouses) and code (notebooks, jobs, repos); Unity Catalog governs what that compute is allowed to see and do.
