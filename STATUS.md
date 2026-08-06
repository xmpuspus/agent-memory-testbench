# Agent Memory Testbench Status

Updated: 2026-08-06

## Current package status (v0.1.9)

- The package, CLI command, and Python import stay `memory-arena` and
  `memory_arena`.
- The bundled result set is `v0.1.8-bundled-historical` with status
  `historical`.
- The bundled snapshot covers 16 questions across 4 categories. Its source
  commits and seed counts are mixed.
- The package does not publish a current benchmark ranking or a current winner.

## Evidence and limitations

The bundled snapshot supports local report, API, and Recall Lab inspection. It
is not a controlled comparison of present-day systems. Do not infer a causal
advantage from individual historical answers, scores, or cross-judge results.

Compatibility notes may refer to legacy result labels and environment variables
needed to read old artifacts. Those labels are not recommendations for a new
benchmark run.

## Six of seven high-severity advisories now clear, and the seventh cannot reach this build

`npm audit` reported seven high-severity findings in the web dependency tree
before this release. Six are now cleared. One remains and is accepted below.

The site is a static export. `web/next.config.mjs` sets `output: "export"`, so
the build emits HTML, CSS, and JavaScript, and neither the wheel nor GitHub
Pages runs a Next.js server.

| Advisory group | Package | Path | Disposition |
| --- | --- | --- | --- |
| DoS through brace expansion | `brace-expansion` | dev, through `eslint` and `glob` | Cleared by `npm audit fix` |
| Quadratic parse in merge keys | `js-yaml` | dev, through `eslint` | Cleared by `npm audit fix` |
| Command injection in the glob CLI | `glob` | dev, through `@next/eslint-plugin-next` | Cleared by a scoped override to `glob@^10.5.0` |
| Same, through the plugin | `@next/eslint-plugin-next` | dev, lint only | Cleared with the same override |
| Same, through the config | `eslint-config-next` | dev, lint only | Cleared with the same override |
| Source-map path traversal and stringify XSS | `postcss` | build only, through `tailwindcss` and `next` | Cleared by `postcss@^8.5.26` plus an override for the copy nested under `next` |
| 21 advisories in Next.js itself | `next` 14.2.35 | build and client bundle | **Accepted.** See below |

The `glob` override is scoped to `@next/eslint-plugin-next` rather than global.
A global override forced `glob@10` onto `rimraf@3.0.2`, which calls `glob` as a
function. `glob@10` exports an object, so `rimraf` threw a `TypeError`. Under
the scoped override `rimraf` keeps `glob@7.2.3` and runs.

### Why the Next.js advisory does not reach what ships

No fixed version exists inside Next.js 14 or 15. The vulnerable range is
`9.3.4-canary.0` through `16.3.0-preview.10`, and the first fixed release is
16.3.0, two major versions ahead.

All 21 advisories need a running Next.js server. They cover the Image
Optimization API, React Server Component streaming and caching, middleware and
proxy handling, Server Actions, rewrites, WebSocket upgrades, and the Edge
runtime. A static export runs none of those.

Two of the 21 touch client code. Neither applies here.

- `GHSA-ffhc-5mcf-pf4q` needs an App Router application that sets a CSP nonce.
  This site sets no nonce.
- `GHSA-gx5p-jg67-6x7h` needs a `next/script` tag with `beforeInteractive` and
  untrusted input. This site uses no `next/script` tag.

A search of `web/app`, `web/components`, and `web/lib` finds no middleware
file, no Server Action, no `next/image` call, no rewrite, no i18n
configuration, and no CSP nonce. `images.unoptimized` is `true`, so the Image
Optimizer never runs.

Accepted for v0.1.9. Moving to Next.js 16 is a v0.2 task, because it changes
the build and the generated bundle, and this release publishes no new
benchmark evidence that a bundle change could disturb.

## Planned work

v0.2.0 is planned work only. Its proposed scope is a controlled benchmark run
with a larger question set, declared system versions, consistent seeds, explicit
cost accounting, and a documented cross-judge protocol. No v0.2.0 benchmark
result shipped yet.
