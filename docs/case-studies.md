# Memory Arena: Historical Case Studies

These four examples are preserved from `v0.1.8-bundled-historical`. That
snapshot has 16 questions across 4 categories and combines mixed source
commits and seed counts. It is useful for inspecting historical answers, but it
does not prove a current ranking, a product recommendation, or a causal
claim about an architecture.

To inspect a case in the UI, run `memory-arena demo`, open the Recall Lab page,
choose the relevant strategy, and inspect the named question record. When a
seed file exists, the bundled raw records are in
`memory_arena/data/results_snapshot/longmemeval-s_<strategy>_seed0.json`.
Treat the answer and retrieval fields as observations from that historical run.

## Case 1: `6aeb4375`

**Question:** How many Korean restaurants have I tried in my city?

**Category:** `knowledge_update`
**Historical reference answer:** `four`

This example is kept to inspect how the bundled run handled an attribute in
a conversational fact. It does not show that any write-time or read-time
method will have the same behavior on another corpus.

### Historical observations

Descriptive evidence from `v0.1.8-bundled-historical`; these observations are
not causal findings or product recommendations. Scores list recorded accuracy
and session recall at 5.

- `mem0` recorded no information about restaurant visits and mentioned Korean
  BBQ beef instead: accuracy `0.04`, session recall at 5 `1.00`.
- `naive_vector` recorded "four different Korean restaurants": accuracy
  `0.80`, session recall at 5 `1.00`.

## Case 2: `830ce83f`

**Question:** Where did Rachel move to after her recent relocation?

**Category:** `knowledge_update`
**Historical reference answer:** `the suburbs`

The source conversations contain an earlier and a later location. Use this case
to review update handling and citations in the historical records. It does not
prove that a particular storage design resolves temporal conflicts.

### Historical observations

Descriptive evidence from `v0.1.8-bundled-historical`; these observations are
not causal findings or product recommendations. Scores list recorded accuracy
and session recall at 5.

- `mem0` recorded the suburbs and cited an earlier Chicago memory: accuracy
  `0.76`, session recall at 5 `1.00`.
- `naive_vector` returned both Chicago and the suburbs, then stated Chicago as
  the direct answer: accuracy `0.32`, session recall at 5 `1.00`.

## Case 3: `e47becba`

**Question:** What degree did I graduate with?

**Category:** `information_extraction`
**Historical reference answer:** `Business Administration`

This is a single-fact retrieval example. It is suitable for inspecting an
individual response, not for concluding that a method generalizes to all
single-fact questions.

### Historical observations

Descriptive evidence from `v0.1.8-bundled-historical`; these observations are
not causal findings or product recommendations. Scores list recorded accuracy
and session recall at 5.

- `mem0g` recorded "Business Administration": accuracy `0.80`, session recall
  at 5 `1.00`.
- `persona_profile` recorded that it could not confirm the degree despite a
  retrieved session that mentioned it: accuracy `0.32`, session recall at 5
  `1.00`.

## Case 4: `118b2229`

**Question:** How long is my daily commute to work?

**Category:** `information_extraction`
**Historical reference answer:** `45 minutes each way`

This example exposes differences among historical retrieved material and
answers. The bundle cannot determine whether a difference came from retrieval,
generation, judging, or another run condition.

### Historical observations

Descriptive evidence from `v0.1.8-bundled-historical`; these observations are
not causal findings or product recommendations. Scores list recorded accuracy
and session recall at 5.

- `mem0` recorded a four-month commute to Roppongi but no duration: accuracy
  `0.08`, session recall at 5 `1.00`.
- `bm25` recorded that the duration was not specified and listed
  `answer_40a90d51` among supporting sessions: accuracy `0.08`, session recall
  at 5 `1.00`.

## Using these examples responsibly

Compare each candidate on representative questions under one declared
protocol, then inspect the returned sources and answers. v0.2.0 is planned
work for a controlled benchmark and is not a published result.
