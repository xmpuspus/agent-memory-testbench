# Memory Arena Status

Updated: 2026-08-05

## Current package status (v0.1.9)

- The package, CLI command, and Python import remain `memory-arena` and
  `memory_arena`.
- The bundled result set is `v0.1.8-bundled-historical` with status
  `historical`.
- The bundled snapshot covers 16 questions across 4 categories and has mixed
  source commits and seed counts.
- The package does not publish a current benchmark ranking or a current winner.

## Evidence and limitations

The bundled snapshot supports local report, API, and Recall Lab inspection. It
is not a controlled comparison of present-day systems. Do not infer a causal
advantage from individual historical answers, scores, or cross-judge results.

Compatibility notes may refer to legacy result labels and environment variables
needed to read old artifacts. Those labels are not recommendations for a new
benchmark run.

## Planned work

v0.2.0 is planned work only. Its proposed scope is a controlled benchmark run
with a larger question set, declared system versions, consistent seeds, explicit
cost accounting, and a documented cross-judge protocol. No v0.2.0 benchmark
result has shipped.
