The knowledge graph models/shapes can be of different types.

Ref: https://graphrag.com/reference/knowledge-graph/

## Domain Graph
A Domain Graph contains Business Domain Knowledge. It contains real-world entities and the relationships between them. 
Frequently used example Domain Graphs are the Movie Graph or the Northwind Graph.
Since Domain Graphs will look different based on the underlying domain, it isn’t possible to provide a blueprint of how one would look. Just keep in mind that they contain structured data adhering to a schema.
![Domain Graph](https://graphrag.com/_astro/domain-graph.DOzUcy6K_YkdvU.svg)


# Lexical Graph
It is useful to chunk large documents into smaller pieces for creating embeddings. An embedding is a text’s semantic representation capturing the meaning of what the text is about. If the given text is long and contains too many diverse subjects, the informative value of its embedding deteriorates.
![Lexical Graph](https://graphrag.com/_astro/knowledge-graph-lexical-graph.De_a3uWZ_Z2h45bE.svg)

![Document Node](https://graphrag.com/_astro/element-document-node.EX6lWBy1_Z1tHYGY.svg)
Document nodes contain the document name and its source. They may contain additional metadata.
![Chunk Node](https://graphrag.com/_astro/element-chunk-node.D0fbLgMU_5u1eG.svg)
Chunk nodes contain the human readable text of a chunk and its vector embedding. They may contain additional metadata.

![Part Of Relationship](https://graphrag.com/_astro/element-part-of-relationship.DZmhpBxU_VhNpd.svg)
The PART_OF relationships do not require additional properties. However, they may contain additional metadata.


## Parent-Child Lexical Graph
When chunking documents, split them into (bigger) chunks (aka Parent Chunks) and further split these chunks into smaller chunks (aka Child Chunks). Use an embedding model to embed the text content of the Child Chunks. Note, it is not necessary to embed the Parent Chunks since they are only used for the answer generation and not for the similarity search.
![Parent Child Lexical Graph](https://graphrag.com/_astro/knowledge-graph-lexical-graph-parent-child.BU743WMk_175fxy.svg)

## Lexical Graph with Sibling Structure
It is useful to keep track of adjacent chunks for a possible retrieval of them. This pattern is an evolution of the Lexical Graph
![Lexical Graph with Sibling Structure](https://graphrag.com/_astro/knowledge-graph-lexical-graph-sibling-structure.BlvN-GwY_Z21kpFr.svg)

## Lexical Graph with Extracted Entities
The biggest problem with the vector search approach as in the e.g. Basic Retrievers or Parent-Child Retrievers is finding all relevant context that is necessary to answer a question. The context can be spread across many chunks not being found by the search. Relating the real-world entities from the chunks to each other and retrieving these relationships together with a vector search provides additional context about these entities that the chunks deal with.
![Lexical Graph with Parent Child](https://graphrag.com/_astro/knowledge-graph-lexical-graph-extracted-entities.BsKeTZFb_ZxxPUk.svg)

![Entity Node](https://graphrag.com/_astro/element-entity-node.CYz1nSiG_ZPvnfF.svg)
Entity nodes contain the name of the entity. Additionally they might contain a description of the entity and a vector embedding (of name and description). They may contain additional metadata. Entity nodes can have additional labels based on the extraction prompt.
![Has Entity Relationship](https://graphrag.com/_astro/element-has-entity-relationship.DdiLLxiJ_Mn4Nw.svg)


## Lexical Graph with Extracted Entities and Community Summaries
Certain questions that can be asked on a whole dataset, do not just relate to things that are present in some chunks but rather search for an overall message that is overarching in the dataset. All aforementioned patterns are not suited to answer these kinds of “global” questions.

Additionally to extracting entities and their relationships, we need to form hierarchical communities within the Domain Graph. This can be done by using the Leiden algorithm. For every community, an LLM summarizes the entity and relationship information into Community Summaries.

![Community Summaries](https://graphrag.com/_astro/knowledge-graph-lexical-graph-extracted-entities-community-summaries.CBUo7m6H_Z2jRSb3.svg)

![Community Node](https://graphrag.com/_astro/element-community-node.moOWVjDw_2cFNJH.svg)

![In Community Relationship](https://graphrag.com/_astro/element-in-community-relationship.BVeLb8W3_Z1gFmKS.svg)

IN_COMMUNITY Relationship The IN_COMMUNITY relationships connect entities to a Community Node that contains a summary. The relationships do not require additional properties. However, they may contain additional metadata. 

![Parent Community Relationship](https://graphrag.com/_astro/element-parent-community-relationship.B8kLK2wP_Z1u2jqV.svg)
PARENT_COMMUNITY Relationship The PARENT_COMMUNITY relationships connects communities of one level to their higher level Community Nodes. The relationships do not require additional properties. However, they may contain additional metadata.

7. Lexical Graph with Hierarchical Structure
8. Lexical Graph with Hypothetical Questions
9. Memory Graph
10. Text Sequence