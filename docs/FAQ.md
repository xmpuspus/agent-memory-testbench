# Memory Arena: FAQ

## What evidence ships with the package?

The package includes `v0.1.8-bundled-historical`, a historical snapshot with
16 questions across 4 categories. Its summaries use mixed source commits
and seed counts. The snapshot supports inspection and regression work; it does
not publish a current benchmark ranking.

## Can I use the bundled numbers to choose a memory system?

No. Use them as examples of a past run only. A decision needs a controlled run
that records the candidate versions, corpus, generator, judge, seeds, costs,
and unavailable systems. Read the [decision guide](decision-guide.md) for a
comparison plan.

## Why is the historical sample small?

The bundle has 16 questions across 4 categories. That sample is too small
and too mixed to support a current winner claim or a general causal conclusion
about an architecture. It remains in the package so users can inspect the
historical evidence and exercise local report paths.

## What does the cross-judge report prove?

Nothing. The legacy cross-judge report is invalid for claims because it compared
incompatible score semantics. It remains quarantined only as invalid legacy
evidence. New runs should keep equivalent raw scores, find every ungraded
record, and compare judges under a declared protocol.

## Why are vendor costs difficult to compare?

Some systems make internal model calls outside the harness accounting path.
Treat a reported cost as incomplete unless the run records every provider call
under a shared accounting method.

## What is the difference between agent memory and RAG?

Both retrieve information. Agent memory is usually built from a user's changing
conversation history, while RAG commonly searches a mostly static document
corpus. The distinction matters when a product must handle updates,
contradictions, source isolation, and deletion requests.

## Is v0.2.0 available?

No. v0.2.0 is planned work for a controlled benchmark with a larger question
set and explicit comparability rules. It has not shipped and it has no current
ranking.
