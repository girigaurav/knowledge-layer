## Knowledge Graph

Ref: https://neo4j.com/blog/genai/what-is-knowledge-graph/

A knowledge graph is an organized representation of real-world entities and their relationships. It is typically stored in a graph database, which natively stores the relationships between data entities. Entities in a knowledge graph can represent objects, events, situations, or concepts. The relationships between these entities capture the context and meaning of how they are connected.

A knowledge graph stores data and relationships alongside frameworks known as **organizing principles**. They can be thought of as rules or categories around the data that provide a flexible, conceptual structure to drive deeper data insights. The usefulness of a knowledge graph lies in the way it organizes the principles, data, and relationships to surface new knowledge for your user or business. The design is useful for many usage patterns, including real-time applications, search and discovery, and opens in new tabgrounding generative AI for question-answering.

You might hear about enterprise-wide structures that consolidate and connect information across data silos and various sources. While that does describe a knowledge graph (one that can underpin a data integration use case), it describes one with a wide scope. You can also build one with a much smaller scope to solve a use-case-specific problem.

## Key characteristics
The definition of knowledge graphs varies depending on whom you ask, but we can distill the essence into three key components: nodes, relationships, and organizing principles.

### Nodes & Relationships

### Organizing Principals
Organizing Principles are a framework, or schema, that organizes nodes and relationships according to fundamental concepts essential to the use cases at hand. Unlike many data designs, knowledge graphs easily incorporate multiple organizing principles.

Organizing principles range from simple (product line -> product category -> product taxonomy) to complex (a complete business vocabulary that explains the data in the graph). Think of an organizing principle as a conceptual map or metadata layer overlaying the data and relationships in the graph.

![Organizing principles as a conceptual map over a knowledge graph](https://dist.neo4j.com/wp-content/uploads/20240722083709/kg-organizing-principle-1.png)

### What about Ontologies?
When learning about knowledge graphs, you might come across articles on ontologies and wonder where they fit in. An ontology is a formal specification of the concepts and the relationships between them for a given subject area; semantic networks are a common way to represent ontologies. Put simply, ontologies are a type of organizing principle.

Ontologies can be complex and require a great deal of effort to define and maintain. When deciding whether an ontology is needed, it’s critical to consider the problems you’re trying to solve with a knowledge graph. In many cases, it won’t be necessary. 

Let’s see what a knowledge graph might look like. Below is a simple knowledge graph of the e-commerce example that shows nodes as circles and relationships between them as arrows. The **organizing principles are also stored as nodes and relationships**, so the illustration uses some color shading to show which nodes and relationships are the instance data and which are the organizing principles:


![Knowledge Graph with Organizing Principle](https://dist.neo4j.com/wp-content/uploads/20240722075316/knowledge-graph-example-1.png)

## Knowledge Graph Construction

![alt text](image-12.png)

White Paper Summary — Knowledge Graph + RAG

The paper proposes a Knowledge Graph + Vector DB based RAG approach for answering customer-support questions more accurately than traditional RAG.

# White Paper Summary — Knowledge Graph + RAG

Ref: https://arxiv.org/pdf/2404.17723

The paper proposes a **Knowledge Graph + Vector DB based RAG** approach for answering customer-support questions more accurately than traditional RAG.

## 1. Knowledge Graph Construction — Done Beforehand

Suppose we have historical support tickets:

- **ENT-22970:** "CSV upload error, updating user email"
- **ENT-1744:** "HTTP POST CSV upload error – internal error"
- **ENT-3547:** "Learning 'upload csv' option fails"

The system parses **ENT-22970** into a structured ticket tree:

```text
ENT-22970
├── Summary: CSV upload error
├── Priority: Major
├── Root Cause: Data Issue
├── Impact Area: Strategic
├── Comments
└── Steps to Reproduce
```

It also identifies relationships between tickets:

```text
ENT-22970
├── SIMILAR_TO → ENT-1744
├── SIMILAR_TO → ENT-3547
└── CLONE_FROM → another ticket
```

The text is also converted into **embeddings** and stored in the **Vector DB**.

So, the construction layer creates:

> **Graph DB → structure + relationships**  
> **Vector DB → semantic representation for search**

## 2. Retrieval — When a User Asks a Question

The user asks:

> "How do I reproduce the issue where the user saw 'CSV upload error in updating user email' and it has Major priority and Data Issue?"

The system first understands the question:

```text
Entity: CSV upload error
Priority: Major
Root Cause: Data Issue
Intent: Steps to Reproduce
```

Then:

```text
Vector DB
    ↓
Finds the relevant ticket → ENT-22970
    ↓
Graph DB
    ↓
Retrieves the relevant fields/relationships
    ↓
Steps to Reproduce
    ↓
LLM
    ↓
Final Answer
```

The LLM can then generate:

> "Open the Dashboard → click Instances → search for users from the CSV → observe that two profiles exist."

## In Simple PM Terms

> **Construction:** Convert historical tickets into a connected knowledge structure and create embeddings.

> **Retrieval:** Understand the question → find the right ticket using Vector Search → use the Knowledge Graph to retrieve the right fields and relationships → LLM generates the answer.

### Key Takeaway

> **Vector DB finds *which ticket is relevant*; Knowledge Graph finds *what information and relationships inside that ticket are relevant*; LLM converts the retrieved evidence into the final answer.**
