# Memory Arena: Decision Guide

Use this guide to choose an architecture to evaluate, not as a list of
benchmark winners. The bundled evidence is the historical snapshot
`v0.1.8-bundled-historical`: 16 questions across 4 categories, assembled from
mixed source commits and seed counts. It does not publish a current ranking.

## Start with your operating constraints

| Constraint | Candidate to evaluate | Why |
| --- | --- | --- |
| Minimal infrastructure | `naive_vector` or `bm25` | Both can be evaluated without vendor-managed graph infrastructure. |
| Mutable user facts | `mem0`, `cognee`, and a vector baseline | Compare explicit update handling with raw-text retrieval on your own update cases. |
| Multi-session reasoning | `graphiti`, `cognee`, and a vector baseline | Evaluate the graph and retrieval approaches under the same dataset and model. |
| Audit-friendly source trail | `karpathy_llm_wiki` and a cited vector baseline | Inspect whether recalled material is understandable to an operator. |
| Strict latency or cost limit | `bm25`, `naive_vector`, and `recency_window` | Establish a low-cost baseline before adding retrieval or generation work. |

These are evaluation starting points, not performance guarantees. Provider
versions, model choices, corpus shape, question mix, and the write path can all
change the result.

## Make the comparison useful

1. Define representative questions, including contradictory facts and
   multi-session questions when those matter to your product.
2. Run the same corpus, generator, judge, seed policy, and cost accounting for
   every candidate.
3. Inspect answers and retrieved sources as well as aggregate scores.
4. Record package versions, source commits, and all unavailable or
   non-comparable runs.

The historical bundle can help test report and Recall Lab workflows, but it is
not enough to select a production architecture today. v0.2.0 is planned
work for a new, controlled benchmark run; it is not a shipped result.
