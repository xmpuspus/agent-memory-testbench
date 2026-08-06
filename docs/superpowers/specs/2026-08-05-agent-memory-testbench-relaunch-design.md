# Agent Memory Testbench public relaunch design

- **Status:** Approved design, implementation not started
- **Date:** 2026-08-05
- **Current package:** `memory-arena`
- **Public display name:** Agent Memory Testbench

## 1. Decision summary

The maintainer published Memory Arena, but did not continue public promotion
after the first release.
The repository has a GitHub release and a PyPI package, so the relaunch must not
say that it never launched. It should say that the project is being rebuilt for
its first meaningful public release.

The relaunch changes the public promise from a vendor ranking to a testbench for
following an agent-memory question from retrieval through answer generation.
The project will help builders compare architecture families, inspect failure
causes, and rerun versioned evidence.

The approved decisions are:

1. Use **Agent Memory Testbench** as the display and site name.
2. Preserve the `memory-arena` PyPI package, `memory-arena` command, and
   `memory_arena` Python import.
3. Rename the GitHub repository to `agent-memory-testbench` at the public
   relaunch, subject to explicit publication approval.
4. Treat v0.1.8 results as historical evidence, not the current leaderboard.
5. Replace the mixed leaderboard with architecture, vendor-system, and
   provider-managed tracks.
6. Make full LongMemEval V1 the first primary evidence track. Keep the local
   30-question set as a developer preflight. Add LongMemEval-V2 Small later as
   a separate agent-trajectory track.
7. Add gold-session and gold-turn controls so retrieval failures can be
   separated from failures to find or use evidence.
8. Publish immutable benchmark snapshots with completeness and validation
   status.
9. Use a reordered README for orientation and a static GitHub Pages site for
   evidence exploration.
10. Record the real keyless `memory-arena demo` journey. Do not record a paid
    benchmark run or hide its duration through frame removal.
11. Preserve the historical changelog. Keep future package entries concise and
    link them to snapshot reports.
12. Release a trust-reset v0.1.9 before the promoted v0.2.0 relaunch.

## 2. Why the project remains useful

The public benchmark category is more crowded than it was when this repository
was created. Agent Memory Benchmark compares multiple memory providers across
several datasets, and LongMemEval-V2 has its own public leaderboard. The project
cannot rely on the claim that no other open harness compares memory systems.

Agent Memory Testbench can still serve a distinct public need:

- Builders need architecture controls, not only provider rankings.
- A single score does not explain whether a system retrieved the wrong session,
  selected the wrong turn, or did not use correct evidence.
- Vendor and model releases make undated leaderboard numbers decay quickly.
- Public results need direct links to versions, raw question records, errors,
  costs, and known limitations.
- A keyless local demo makes the evidence inspectable without API keys or
  Docker.

Keep the project open source and independent of memory vendors. Do not claim
that it is the only independent or open benchmark unless a current landscape
review can prove that statement.

## 3. Research reconciliation

### 3.1 Public state

The repository was created on 2026-06-29 and released as v0.1.8 on GitHub and
PyPI. Its public use remained very low in the 2026-08-05 audit. This is better
described as an under-launched project than an abandoned one. Traffic and
download counts are time-sensitive and belong in dated research notes, not in
the product promise.

### 3.2 The current public claim is not durable

The README currently leads with a claim that a short vector-store implementation
beats every funded memory SDK. That sentence has three problems:

- Vendor versions have already moved.
- Several public rows do not share the same completeness or seed count.
- The 16-question smoke set is too small to support a broad market verdict.

The new public promise does not depend on a vendor remaining at a particular
rank.

### 3.3 The defensible historical finding

The raw v0.1.8 records support a narrower observation. For `naive_vector`, all
gold supporting sessions appeared in the top five on 38 of 48 seeded
question-runs. The project composite on those runs averaged 49.8 out of 100.
This supports the statement that complete session retrieval did not guarantee a
good answer on that smoke test.

It does not support any of these statements:

- Do not say that the system retrieved the exact supporting evidence.
- Do not say that turn-level retrieval was perfect.
- Do not say that any system solves retrieval.
- Do not treat the difference between recall percentage and answer score as a
  reasoning score.

Turn recall was zero in those 38 historical records. The historical report must
use "all gold supporting sessions appeared in the top five," not
"perfect retrieval" or "the exact memory was retrieved."

### 3.4 Integrity problems that block a new public claim

The audit found four protocol problems that must be corrected before promotion:

1. The README describes 16 questions across four categories, while the default
   loader selects at least 30 questions across five categories.
2. The YAML conversion path does not preserve `ground_truth.fact_versions`, so
   knowledge-update scoring differs by loader.
3. `scripts/cross_judge.py` compares the second judge's raw score with the first
   judge's adjusted composite. The published absolute judge difference is not a
   like-for-like comparison.
4. The web client silently returns mock benchmark rows when its data request
   fails or is empty.

The public docs also route readers to the removed `mem0g` row and repeat old
Mem0 leader values that disagree with the README. Correct these files before a
new public push.

The existing `full_context` result is also incomplete because its cost cap
stopped the run after 12 of 16 questions. It cannot support a public claim about
full-context performance until it completes the same protocol as the systems it
is compared with.

### 3.5 Vendor-version drift

The 2026-08-05 audit found these material version gaps:

| System | Published result version | Audit-current version | Relaunch treatment |
| --- | --- | --- | --- |
| Mem0 | `mem0ai==2.0.2` | `2.0.17` | Rerun in vendor track |
| Cognee | result metadata `1.0.3` | `1.4.1` | Rerun in vendor track |
| Graphiti | `graphiti-core==0.13` | `0.29.3` | Rerun in vendor track |

Mem0 had nine stable releases after the published pin. Cognee's larger raw
release count included prereleases; six stable releases followed the June 20
baseline. Graphiti was already far behind its current line even though only one
more stable release landed after June 20. This is why Graphiti belongs in
the first vendor refresh with Mem0 and Cognee.

These versions are a dated audit record. The site must show a
`versions_checked` date and refresh the data before implementation begins.

### 3.6 Name collision

An academic benchmark named MemoryArena was published before this repository.
The public rebrand reduces confusion without breaking existing package users.
An exact-name check on 2026-08-05 found no GitHub repository or PyPI project
named Agent Memory Testbench. This is a collision scan, not trademark advice.

## 4. Goals and exclusions

### 4.1 Goals

The relaunch succeeds when:

- A visitor understands the project in the first README screen.
- A user can launch the bundled site with two commands and no credentials.
- Every current public result shows its track, protocol, snapshot, question
  count, seed count, versions, completeness, and validation status.
- A user can inspect one question from expected evidence through retrieved
  evidence, generated answer, and judge result.
- Raw records regenerate every published summary.
- Historical and partial results are not mixed into current rankings.
- A vendor or architecture maintainer can reproduce the adapter configuration
  and submit a current result for validation.
- The project has an explicit process for noticing and reporting dependency and
  provider drift.

### 4.2 Exclusions

The relaunch will not:

- Claim universal memory-system rankings.
- Compare V1 and V2 results as if they share one protocol.
- Mix architecture-controlled and provider-managed results in one ranking.
- Promise causal traffic or star growth from README length, graphics, or a site.
- Rename the PyPI project, CLI command, or Python module.
- Rename internal Python classes solely for branding.
- Publish a new numerical claim before the evidence gate passes.
- Add custom analytics as a launch need.
- Use a custom domain in the first release.
- Publish, rename the repository, or post announcements without explicit final
  approval.

## 5. Public identity and compatibility

### 5.1 Name and promise

The display name is **Agent Memory Testbench**.

The primary line is:

> Benchmark agent memory from retrieval to answer.

The supporting description is:

> Compare memory architectures, trace where answers fail, and rerun versioned
> evidence from one open testbench.

### 5.2 Compatibility map

| Surface | Relaunch value |
| --- | --- |
| Display and site name | Agent Memory Testbench |
| GitHub repository | `agent-memory-testbench` at v0.2.0 publication |
| PyPI project | `memory-arena` |
| CLI | `memory-arena` |
| Python import | `memory_arena` |
| Transition note | "Formerly Memory Arena" for v0.1.9 and v0.2.x |
| Protocol identifiers | Corpus and method based, not brand based |

GitHub redirects will preserve old repository URLs after the rename. The README
and release notes must still state the package name because the display name and
install command differ.

## 6. Benchmark architecture

### 6.1 Data flow

```text
corpus source
  -> canonical QuestionRecord set
  -> protocol manifest and preflight validation
  -> strategy execution within one benchmark track
  -> per-question retrieval and answer records
  -> primary and secondary judging
  -> completeness, cost, and integrity validation
  -> immutable snapshot
  -> static site export, bundled demo, README graphics, and release report
```

Each stage writes or consumes a defined artifact. The public site does not
calculate new benchmark numbers in the browser. It reads summaries that were
validated against raw records.

### 6.2 Benchmark tracks

#### Architecture track

This is the primary public evidence. Architectures use the same corpus,
generation model, judge, prompts, retrieval limits, and reporting rules.

The first full V1 track has:

- No-memory control
- Full-context control
- Gold-session oracle
- Gold-turn oracle
- Recency
- BM25
- Dense vector
- Hybrid retrieval
- Hierarchical memory
- Graph memory

The list favors one representative per architecture family. More
implementations may appear in an experimental appendix without expanding the
primary table.

#### Vendor-system track

This track starts with Mem0, Cognee, and Graphiti at current stable versions.
Report vendor-owned model calls, hidden storage services, or internal costs as
confounds. A vendor row cannot appear in the architecture table.

A vendor enters the current table only when:

- Document its version and intended configuration.
- Install it in a supported environment.
- Complete the needed corpus and seed count.
- Keep failures and retries.
- Separate direct and unknown internal costs.

The first vendor snapshot uses all 500 V1 questions and three complete seeds
for every displayed vendor. If cost limits the run, reduce the number of vendors
rather than the question or seed count.

#### Provider-managed memory track

Provider-managed systems, including Anthropic Memory Stores, combine memory,
model, hosting, and runtime behavior. Evaluate them within provider-specific
conditions. Do not present them as a controlled architecture comparison.

### 6.3 Corpus policy

The existing result sets receive these roles:

| Data set | Role after trust reset |
| --- | --- |
| Historical 16-question V1 smoke | Archived v0.1.8 evidence |
| Local 30-question, five-category set | Developer preflight and regression fixture |
| Full 500-question LongMemEval V1 | Primary v0.2.0 architecture evidence |
| LongMemEval-V2 Small | Separate v0.3.0 trajectory track |

Every public table uses one canonical question manifest. Alternate loaders must
produce the same records, including `fact_versions`, constraints, supporting
session IDs, and supporting turn IDs.

### 6.4 Diagnostic controls

The four controls answer different questions:

| Control | Input to answer generation | Diagnostic purpose |
| --- | --- | --- |
| No memory | Question only | Lower reference |
| Full context | Available conversation within declared budget | Context-stuffing reference |
| Gold session | All labelled supporting sessions | Remove session-selection failure |
| Gold turn | Exact labelled supporting turns | Remove evidence-location failure |

Do not call `full_context` a ceiling. Do not call gold-session recall exact
evidence retrieval. The project reports conditional answer performance and
oracle comparisons rather than subtracting recall percentages from answer
scores.

## 7. Metrics and judging

### 7.1 Public metric hierarchy

| Metric group | Public fields | Interpretation |
| --- | --- | --- |
| Answer | Raw 0 to 100 judge score | Primary answer-quality measure |
| Task-adjusted | Structural, source, temporal, update, and abstention adjustments | Project-specific composite |
| Retrieval | Session and turn recall@5, MRR, NDCG | Evidence selection quality |
| Reliability | Completion rate, errors, retries | Operational consistency |
| Efficiency | Direct cost, unknown internal cost, latency | Resource use |
| Uncertainty | Question confidence interval and seed variance | Measurement uncertainty |

Do not label the existing adjusted composite only as "accuracy." Publish and
version the formula in the protocol.

### 7.2 Cross-judge rules

- Both judges grade the same stored answers.
- Compare raw answer score with raw answer score.
- The secondary judge grades every question for one common seed across every
  displayed architecture.
- The report includes means, rank correlation, per-question disagreement, and
  grade count.
- Recompute adjusted scores from each judge's raw score when you need an
  adjusted comparison.
- Record missing or failed grades as ungraded. Do not convert them to zero.
- If judge order differs, the release reports the difference.

### 7.3 Completeness rule

The primary architecture table needs the full V1 question set and three
complete seeds for every displayed system. Mark a run as `partial` and exclude
it from the default ranking when cost, provider error, timeout, or missing data
stops it.

If the complete run is too expensive, the release benchmarks fewer
representative systems. It does not lower the completeness rule for selected
rows.

## 8. Snapshot and evidence model

### 8.1 Identifiers

Three identifiers are displayed together:

| Identifier | Example | Purpose |
| --- | --- | --- |
| Package version | `0.2.0` | Installed software and public UI |
| Protocol version | `amt-v1.0` | Scoring and execution contract |
| Snapshot ID | `lme-v1-full-2026-09-r1` | Immutable benchmark run set |

Package releases, protocol changes, and result refreshes are related but not
interchangeable.

### 8.2 Snapshot contents

Each snapshot has:

- `manifest.json` with corpus and question hashes
- Exact strategy and provider versions
- Exact model identifiers where providers expose them
- Prompts, temperatures, seeds, retrieval limits, and cost caps
- Per-question retrieval, answer, judge, cost, latency, error, and retry records
- Derived summaries and confidence calculations
- Completeness matrix
- Cost ledger that shows unknown vendor costs
- Validation report
- Known limitations
- Source commit
- Reproduction and summary-regeneration commands

Never overwrite snapshots. A newer run creates a new ID and may mark an
older snapshot `superseded`.

### 8.3 Public statuses

| Status | Meaning | Default ranking behavior |
| --- | --- | --- |
| Checked | Complete and passed all validators | Included |
| Partial | Useful run that did not meet completeness | Excluded |
| Historical | Preserved result from an older protocol or release | Excluded |
| Superseded | Replaced by a newer comparable snapshot | Excluded |

### 8.4 Failure behavior

- Loader count or hash mismatch fails the preflight.
- Missing version or protocol metadata fails verification.
- Cost-cap termination makes the affected strategy partial.
- Keep a provider failure with its question ID and retry count.
- Mark missing retrieval IDs as unmeasurable. Do not score them as zero recall.
- Mark judge failure as ungraded. Do not score it as a wrong answer.
- Summary mismatch fails the snapshot.
- Checksum mismatch makes the site reject the snapshot.
- Static-site data failure displays an unavailable state. It never substitutes
  mock benchmark rows.

## 9. README design

### 9.1 First screen

The first screen has, in order:

1. Agent Memory Testbench
2. "Formerly Memory Arena" transition note
3. "Benchmark agent memory from retrieval to answer"
4. One-sentence description
5. Latest evidence-status badge
6. Demo recording
7. Links to checked results, local demo, and benchmark method
8. The keyless commands:

```bash
pip install memory-arena
memory-arena demo
```

No new numerical result appears above the fold until checks pass for its snapshot.

Durable badges cover package version, CI, Python support, license, and latest
checked snapshot. Strategy and test-count badges are removed because they
drift.

### 9.2 README order

The remaining sections are:

1. Latest checked finding
2. Try it locally
3. Choose a path: compare, trace, reproduce, or contribute
4. What the testbench measures
5. Benchmark tracks
6. Execution lifecycle
7. Add an architecture or adapter
8. Evidence and reproducibility
9. Boundaries and limitations
10. Citation, license, and acknowledgements

The README has no arbitrary line target. Detailed configuration inventories,
old result narratives, and specialized experimental notes move to focused docs
or snapshot reports.

## 10. GitHub Pages design

The first hosted URL is:

`https://xmpuspus.github.io/agent-memory-testbench/`

v0.2.0 does not need a custom domain.

### 10.1 Navigation

- Overview
- Results
- Failure Lab
- Snapshots
- Benchmark method
- GitHub

Existing `/benchmark` and `/recall-lab` paths redirect to their replacements.

### 10.2 Overview

The home page has the public promise, latest checked snapshot, one
finding, the four diagnostic controls, quickstart, and links to evidence.

### 10.3 Results

The default view is the latest checked architecture snapshot. Filters cover
snapshot, track, category, strategy family, metric, and evidence status.

Every row displays answer score, retrieval measures, completion rate, cost,
latency, seeds, version, confidence interval, and verification status. Vendor
systems appear in a separate table. Historical and partial data need an
explicit filter.

### 10.4 Failure Lab

The Failure Lab follows one question through:

1. Question and expected answer
2. Gold sessions and turns
3. Retrieved sessions and turns
4. Generated answer
5. Primary and secondary judge results
6. Structural or category-specific failures
7. Cost, latency, model, and strategy version

Filters include correct-session/wrong-answer, correct-session/wrong-turn,
retrieval miss, judge disagreement, update failure, temporal failure, and
abstention failure.

### 10.5 Snapshots and benchmark method

The snapshot page exposes status, protocol, corpus, included systems,
completion, versions, costs, limitations, raw records, and reproduction
commands.

The benchmark method page explains formulas, intervals, judge comparison, cost
boundaries, and the separation of benchmark tracks. It links to deeper source
documentation rather than duplicating it.

### 10.6 Public-site trust rules

- Snapshot identity remains visible in the page header.
- Results always show question count and completeness.
- Every chart links to its source snapshot.
- Stable snapshot URLs are shareable.
- Mark mock data visibly in development so users cannot mistake it for public
  evidence.
- On mobile pages, rank the finding, status, and filters first.

## 11. Recording and static asset design

### 11.1 README recording

The README recording is a 15 to 20 second, real-time journey:

1. Run `memory-arena demo`.
2. Open the bundled overview.
3. Enter Results.
4. Select "Correct session, wrong answer."
5. Open one Failure Lab record.
6. Hold on "Inspect the evidence locally. No API key. No Docker."

The recording does not show a benchmark executing. It does not remove frames to
hide time or use a long automated page scroll.

The GIF is 960 by 540 pixels, 10 to 12 frames per second, and targets less than
6 MB. Include a matching static poster.

### 11.2 Recording proof

Produce the recording from a clean environment using the built wheel. Unset API
keys. Do not use Docker. Check that the bundled snapshot matches the displayed
snapshot ID. Verification reads back representative frames and checks
duration, frame count, dimensions, size, text legibility, and the absence of
credentials or local paths.

After installation, disable network access and run the demo again. This check
proves that the bundled site and snapshot do not need a live API.

### 11.3 Visual rules

The visual system uses:

- Navy for controlled architectures
- Neutral gray for controls
- Green for oracle conditions
- Teal for vendor systems
- Purple for provider-managed systems
- Red only for validation failures
- Labels and shapes in addition to color
- Direct data labels instead of distant legends
- Snapshot ID and evidence status on result graphics

The first new evidence chart is the diagnostic ladder: no memory, actual
retrieval, gold sessions, and gold turns. It does not compare recall percentage
and answer score as if they share one scale.

### 11.4 Asset set

| Asset | Format |
| --- | --- |
| README demo | 960 by 540 GIF |
| Demo poster | 960 by 540 PNG |
| GitHub social preview | 1280 by 640 PNG, under 1 MB |
| LinkedIn launch video | 1080 by 1350 MP4, 20 to 30 seconds |
| LinkedIn thumbnail | 1080 by 1350 PNG |
| Evidence card | 1080 by 1350 PNG |
| Overview, results, failure, snapshot captures | 1440 by 900 PNG |

Each snapshot-specific media directory has a manifest with snapshot ID,
source commit, input files, generation command, dimensions, file size, SHA-256,
alt text, creation date, and validation results.

### 11.5 LinkedIn video

The 20 to 30 second, 4:5 video uses this order:

1. "Finding the right memory is not the same as using it."
2. Show the four-step diagnostic ladder.
3. Open one correct-session, wrong-answer record.
4. Show the snapshot ID and reproduction details.
5. End on `pip install memory-arena`.

The video must work without audio. Burn captions into the video and keep an SRT
sidecar with the source assets.

## 12. Changelog and release model

### 12.1 Changelog

The existing 410-line changelog remains intact. Future entries use Added,
Changed, Fixed, Evidence, Compatibility, and Known limitations. Detailed
benchmark numbers live in immutable snapshot reports.

Each release entry links the package version, protocol version, and snapshot ID.

GitHub release notes use this order:

1. Why the release matters
2. Software changes
3. Install or upgrade commands
4. Compatibility notes
5. Checked snapshot summary
6. Raw evidence link
7. Known limitations
8. Independent reproduction command

Link every numerical release claim to its snapshot report.

### 12.2 v0.1.9 trust reset

This maintenance release is not promoted as the new benchmark. It has:

- Display-name transition
- Historical status for v0.1.8 results
- Corrected loader parity and update metadata
- Corrected cross-judge comparison
- Explicit static-data failure behavior
- Current decision guide, FAQ, case studies, and status docs
- Snapshot identity in the bundled demo
- Compatibility and deprecation notices

It does not advertise a new ranking.

### 12.3 v0.2.0 public relaunch

The promoted release needs:

- Full V1 architecture snapshot
- Three complete seeds per displayed architecture
- Four diagnostic controls
- Immutable manifest and validation report
- Valid secondary-judge comparison
- Redesigned Failure Lab
- GitHub Pages
- Reordered README
- Checked recording and static assets
- Clean-wheel reproduction
- GitHub repository rename, after explicit approval

### 12.4 v0.2.x evidence updates

Mem0, Cognee, and Graphiti receive the first current vendor snapshot. Each
refresh publishes version differences, configuration changes, completion,
errors, direct and unknown costs, and a maintainer-review link.

Provider-managed memory follows as a separate track and does not delay v0.2.0.

### 12.5 v0.3.0 V2 track

LongMemEval-V2 Small receives separate trajectory, multimodal, scoring, and
evidence work. External leaderboard submission happens only after the local and
submission checks prove that both record sets are the same.

## 13. Ongoing relevance policy

The relaunch includes a maintenance policy so the same drift does not recur:

- Check vendor and provider releases monthly.
- Display the last version-check date publicly.
- Create a new snapshot when a selected provider has a material stable release,
  a provider deprecates a model, the protocol changes, or a corpus changes.
- If no trigger happens, review current snapshots at least quarterly.
- Never update a displayed package version without a matching run.
- Mark an affected snapshot historical or superseded when its environment is no
  longer representative.
- Generate public strategy counts and category counts from manifests rather
  than hand-maintaining them in several files.
- Review stale links, install commands, and bundled-demo status at every package
  release.

Monthly checks are read-only until a maintainer approves a rerun and its cost.

## 14. Delivery sequence and gates

### 14.1 Work sequence

1. Trust reset and compatibility work
2. Protocol and snapshot infrastructure
3. Oracle controls and full V1 evidence run
4. Results and Failure Lab site
5. README and documentation
6. Recording and static assets
7. Independent verification
8. Release preparation
9. Explicit publication approval

### 14.2 Integrity gate

- Canonical question counts and hashes agree across loaders.
- `fact_versions` and constraints survive every path.
- Cross-judge comparisons use equivalent score fields.
- Static data failure cannot display unlabelled mock results.
- Current guidance has no removed system or stale leader.

### 14.3 Protocol gate

- Protocol manifest is complete.
- Test controls in isolation.
- Metric names and formulas match public copy.
- Define error, retry, cost, and completeness fields.

### 14.4 Evidence gate

- Every displayed architecture completes every needed question and seed.
- Summary files regenerate from raw records.
- Secondary-judge input records match the primary answer records.
- Full-context completes all questions.
- Snapshot hashes and validation report pass.

### 14.5 Package gate

- Source and wheel distributions build and pass metadata checks.
- A clean environment installs the wheel.
- `memory-arena demo` works without keys or Docker.
- The bundled snapshot ID and contents match the release.

### 14.6 Public-surface gate

- Inspect the README, site, recording, captures, links, mobile layout, and
  accessibility against the same snapshot.
- Read representative frames and pages back visually.
- No claim appears without scope and evidence.

### 14.7 Publication gate

Package upload, GitHub release, repository rename, social-preview upload, and
public announcement need explicit approval after every earlier gate passes.

## 15. Verification plan

Implementation must add or update checks for:

- Loader parity, count, category distribution, and question hashes
- Preservation of `fact_versions`, supporting sessions, and supporting turns
- Raw judge versus raw judge comparison
- Adjusted score formula versioning
- Missing-grade and unmeasurable-recall behavior
- Snapshot schema and completeness validation
- Deterministic summary regeneration
- No static-site fallback to unlabelled mock data
- Correct track separation and default filters
- Historical and partial status exclusion
- Clean wheel and keyless demo
- Static export under the GitHub Pages base path
- Redirects for old routes
- Link, accessibility, viewport, and media-dimension checks
- Changelog, package, protocol, and bundled-snapshot alignment

Paid benchmark execution needs a preflight estimate and separate cost
approval. Verification does not authorize publication.

## 16. Risks and responses

| Risk | Response |
| --- | --- |
| Full V1 costs more than expected | Reduce displayed architectures, not completeness |
| Provider versions move during the run | Freeze versions in the snapshot and publish the run date |
| A provider cannot expose retrieval IDs | Mark retrieval unmeasurable and keep it out of retrieval rankings |
| Judges disagree | Publish both results and the disagreement |
| Full-context exceeds limits | Declare the budget and mark incomplete runs partial |
| GitHub Pages data is stale | Bind every build to an immutable snapshot ID |
| Public name has a later conflict | Keep package compatibility and reassess before repository rename |
| Rebrand hides package name | Put the install name next to every first-use call to action |
| Media becomes stale | Bind media to a snapshot manifest and regenerate only for a new snapshot |
| Growth remains low | Judge the release first on evidence quality and usability, then use dated traffic data to adjust distribution |

## 17. Public outcome measurement

The project will review these signals after release without claiming they prove
cause:

- GitHub views and unique visitors
- Non-bot clone patterns
- PyPI downloads by release
- GitHub Pages visits if privacy-safe hosting metrics are available
- Clicks from Pages to installation and raw evidence, if available without new
  tracking infrastructure
- Issues that reproduce or question results
- Adapter and configuration contributions
- Snapshot citations or links from external projects

The launch has no arbitrary star target. The first measure of success is that a
skeptical visitor can find, inspect, and rerun the evidence.

## 18. Source references

Repository evidence:

- `README.md`
- `CHANGELOG.md`
- `STATUS.md`
- `docs/decision-guide.md`
- `docs/FAQ.md`
- `docs/case-studies.md`
- `memory_arena/benchmark/questions.py`
- `memory_arena/benchmark/evaluator.py`
- `scripts/cross_judge.py`
- `web/lib/api.ts`
- `web/app/page.tsx`
- `web/app/benchmark/page.tsx`
- `web/app/recall-lab/page.tsx`
- `docs/demo.tape`
- `demo-flow.yaml`
- `scripts/record_dashboard_tour.py`
- `scripts/build_social_preview.py`

External references:

- Academic MemoryArena: <https://memoryarena.github.io/>
- Agent Memory Benchmark: <https://github.com/vectorize-io/agent-memory-benchmark>
- LongMemEval-V2: <https://github.com/xiaowu0162/LongMemEval-V2>
- Anthropic Memory Stores API: <https://platform.claude.com/docs/en/api/beta/memory_stores>
- GitHub social-preview guidance: <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview>
- LinkedIn video specifications: <https://www.linkedin.com/help/linkedin/answer/a424737>
- LinkedIn image guidance: <https://www.linkedin.com/help/linkedin/answer/a527229/sharing-photos-or-videos?lang=en>

## 19. Implementation boundary

This document authorizes design documentation only. It does not authorize code
changes, benchmark spending, package publication, repository rename, GitHub
release creation, or public posting. After this specification is reviewed and
approved, the next artifact is a detailed implementation plan. Implementation
starts only after that plan receives separate approval.
