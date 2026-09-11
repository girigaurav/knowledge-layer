from __future__ import annotations

import random

SEED = 42
NUM_COMMUNITIES = 5
PEOPLE_PER_COMMUNITY = 14
NUM_COMPANIES = 20
NUM_PRODUCTS = 10

INDUSTRIES = ["Software", "Retail", "Finance", "Healthcare"]
CATEGORIES = ["Electronics", "Books", "Home", "Sports"]


def generate() -> dict:
    rng = random.Random(SEED)

    people = [
        {"id": f"p{i}", "name": f"Person{i}", "community": i // PEOPLE_PER_COMMUNITY}
        for i in range(NUM_COMMUNITIES * PEOPLE_PER_COMMUNITY)
    ]
    companies = [
        {"id": f"c{i}", "name": f"Company{i}", "industry": INDUSTRIES[i % len(INDUSTRIES)]}
        for i in range(NUM_COMPANIES)
    ]
    products = [
        {"id": f"prod{i}", "name": f"Product{i}", "category": CATEGORIES[i % len(CATEGORIES)]}
        for i in range(NUM_PRODUCTS)
    ]

    follows = []
    for a in people:
        for b in people:
            if a["id"] == b["id"]:
                continue
            probability = 0.18 if a["community"] == b["community"] else 0.02
            if rng.random() < probability:
                follows.append({"from": a["id"], "to": b["id"]})

    works_at = [
        {"from": p["id"], "to": companies[rng.randrange(len(companies))]["id"]}
        for p in people
    ]

    purchased = []
    for p in people:
        for _ in range(rng.randint(0, 4)):
            product = products[rng.randrange(len(products))]
            purchased.append(
                {"from": p["id"], "to": product["id"], "quantity": rng.randint(1, 5)}
            )

    return {
        "people": people,
        "companies": companies,
        "products": products,
        "follows": follows,
        "works_at": works_at,
        "purchased": purchased,
    }


if __name__ == "__main__":
    data = generate()
    print(
        f"people={len(data['people'])} companies={len(data['companies'])} "
        f"products={len(data['products'])} follows={len(data['follows'])} "
        f"works_at={len(data['works_at'])} purchased={len(data['purchased'])}"
    )
