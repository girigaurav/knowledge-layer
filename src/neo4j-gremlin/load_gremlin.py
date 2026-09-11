from __future__ import annotations

from connections import gremlin_g
from dataset import generate


def load() -> None:
    data = generate()
    g, conn = gremlin_g()

    try:
        g.V().drop().iterate()

        for row in data["people"]:
            (
                g.add_v("person")
                .property("id", row["id"])
                .property("name", row["name"])
                .property("community", row["community"])
                .next()
            )
        for row in data["companies"]:
            (
                g.add_v("company")
                .property("id", row["id"])
                .property("name", row["name"])
                .property("industry", row["industry"])
                .next()
            )
        for row in data["products"]:
            (
                g.add_v("product")
                .property("id", row["id"])
                .property("name", row["name"])
                .property("category", row["category"])
                .next()
            )

        for row in data["follows"]:
            (
                g.V().has("id", row["from"]).as_("a")
                .V().has("id", row["to"])
                .add_e("follows").from_("a")
                .next()
            )
        for row in data["works_at"]:
            (
                g.V().has("id", row["from"]).as_("a")
                .V().has("id", row["to"])
                .add_e("works_at").from_("a")
                .next()
            )
        for row in data["purchased"]:
            (
                g.V().has("id", row["from"]).as_("a")
                .V().has("id", row["to"])
                .add_e("purchased").from_("a")
                .property("quantity", row["quantity"])
                .next()
            )

        node_count = g.V().count().next()
        edge_count = g.E().count().next()
        print(f"gremlin: loaded {node_count} nodes, {edge_count} edges")
    finally:
        conn.close()


if __name__ == "__main__":
    load()
