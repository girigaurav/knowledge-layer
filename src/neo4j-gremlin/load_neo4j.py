from __future__ import annotations

from connections import neo4j_driver
from dataset import generate


def load() -> None:
    data = generate()
    driver = neo4j_driver()
    with driver:
        driver.execute_query("MATCH (n) DETACH DELETE n")

        driver.execute_query(
            "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE"
        )
        driver.execute_query(
            "CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE"
        )
        driver.execute_query(
            "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE"
        )

        driver.execute_query(
            "UNWIND $rows AS row "
            "MERGE (p:Person {id: row.id}) SET p.name = row.name, p.community = row.community",
            rows=data["people"],
        )
        driver.execute_query(
            "UNWIND $rows AS row "
            "MERGE (c:Company {id: row.id}) SET c.name = row.name, c.industry = row.industry",
            rows=data["companies"],
        )
        driver.execute_query(
            "UNWIND $rows AS row "
            "MERGE (p:Product {id: row.id}) SET p.name = row.name, p.category = row.category",
            rows=data["products"],
        )
        driver.execute_query(
            "UNWIND $rows AS row "
            "MATCH (a:Person {id: row.from}), (b:Person {id: row.to}) "
            "MERGE (a)-[:FOLLOWS]->(b)",
            rows=data["follows"],
        )
        driver.execute_query(
            "UNWIND $rows AS row "
            "MATCH (a:Person {id: row.from}), (b:Company {id: row.to}) "
            "MERGE (a)-[:WORKS_AT]->(b)",
            rows=data["works_at"],
        )
        driver.execute_query(
            "UNWIND $rows AS row "
            "MATCH (a:Person {id: row.from}), (b:Product {id: row.to}) "
            "MERGE (a)-[r:PURCHASED]->(b) SET r.quantity = row.quantity",
            rows=data["purchased"],
        )

        node_count = driver.execute_query("MATCH (n) RETURN count(n) AS c").records[0]["c"]
        edge_count = driver.execute_query("MATCH ()-->() RETURN count(*) AS c").records[0]["c"]
        print(f"neo4j: loaded {node_count} nodes, {edge_count} edges")


if __name__ == "__main__":
    load()
