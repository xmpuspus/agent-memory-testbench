"use client";

import { useEffect, useMemo, useState } from "react";
import {
  STRATEGIES,
  STRATEGY_LABELS,
  STRATEGY_COLORS,
  STRATEGY_DESCRIPTIONS,
  CORPORA,
  FAILURE_LABELS,
  fetchBenchmarkResults,
  fetchRecallRecords,
  type BenchmarkDataState,
  type FailureClass,
  type Strategy,
  type RecallRecord,
} from "@/lib/api";
import BenchmarkDataStatus from "@/components/BenchmarkDataStatus";

type Verdict = "HIT" | "MISS" | "N/A";

function verdict(rec: RecallRecord, measurable: boolean | null): Verdict {
  // Strategy-level not measurable (e.g. full_context dumps everything; mem0g
  // hides retrieval inside the SDK). The runner already flags these so the
  // dashboard does not pretend HIT/MISS.
  if (measurable === false) return "N/A";
  if (rec.recall_at_k_measurable === false) return "N/A";
  if (!rec.ir) return "N/A";
  return rec.ir.session_hit_at_k > 0 ? "HIT" : "MISS";
}

function Field({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="space-y-1">
      <div className="font-semibold uppercase tracking-wide opacity-70">
        {label}
      </div>
      <div
        className={`leading-relaxed ${mono ? "font-mono break-all" : ""}`}
        style={{ color: "var(--foreground)" }}
      >
        {value}
      </div>
    </div>
  );
}

function fmtMs(value: number | undefined): string {
  if (value === undefined || value === null) return "—";
  if (value < 1000) return `${value.toFixed(0)}ms`;
  return `${(value / 1000).toFixed(1)}s`;
}

export default function RecallLabPage() {
  const [corpus] = useState(CORPORA[0]?.name ?? "longmemeval-s");
  const [dataState, setDataState] = useState<BenchmarkDataState | null>(null);
  const [availableStrategies, setAvailableStrategies] = useState<string[]>([]);
  const [strategy, setStrategy] = useState<string>("");
  const [data, setData] = useState<{
    recall_at_k_measurable: boolean | null;
    top_k: number | null;
    judge_fail_threshold: number | null;
    failure_counts: Partial<Record<FailureClass, number>>;
    records: RecallRecord[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [failureFilter, setFailureFilter] = useState<FailureClass | "all">("all");

  // Populate strategy dropdown from the benchmark results so we only show
  // strategies that actually have a result file for this corpus.
  useEffect(() => {
    fetchBenchmarkResults(corpus).then((dataState) => {
      setDataState(dataState);
      if (dataState.state === "unavailable") {
        setAvailableStrategies([]);
        setStrategy("");
        setData(null);
        return;
      }
      const names = dataState.rows
        .map((r) => r.strategy as string)
        .filter((n): n is string => typeof n === "string" && n.length > 0);
      // Keep declaration order from STRATEGIES so the dropdown is stable.
      const ordered = (STRATEGIES as readonly string[]).filter((s) =>
        names.includes(s)
      );
      const fallback = ordered.length > 0 ? ordered : names;
      setAvailableStrategies(fallback);
      if (!strategy && fallback.length) {
        // Prefer naive_vector as the default since it's the most pedagogical.
        setStrategy(fallback.includes("naive_vector") ? "naive_vector" : fallback[0]);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [corpus]);

  useEffect(() => {
    if (!strategy) return;
    setLoading(true);
    setNotFound(false);
    fetchRecallRecords(corpus, strategy).then((res) => {
      setLoading(false);
      if (!res) {
        setData(null);
        setNotFound(true);
        return;
      }
      setData({
        recall_at_k_measurable: res.recall_at_k_measurable ?? null,
        top_k: res.top_k ?? null,
        judge_fail_threshold: res.judge_fail_threshold ?? null,
        failure_counts: res.failure_counts ?? {},
        records: res.records ?? [],
      });
    });
  }, [corpus, strategy]);

  const counts = useMemo(() => {
    if (!data) return { hit: 0, miss: 0, na: 0, total: 0 };
    let hit = 0,
      miss = 0,
      na = 0;
    for (const r of data.records) {
      const v = verdict(r, data.recall_at_k_measurable);
      if (v === "HIT") hit++;
      else if (v === "MISS") miss++;
      else na++;
    }
    return { hit, miss, na, total: data.records.length };
  }, [data]);

  const measurable = data?.recall_at_k_measurable;

  const visibleRecords = useMemo(() => {
    if (!data) return [];
    if (failureFilter === "all") return data.records;
    return data.records.filter((r) => r.failure_class === failureFilter);
  }, [data, failureFilter]);

  // Offer only the classes this strategy actually produced, so no filter
  // promises records that do not exist.
  const filterOptions = useMemo(() => {
    const counts = data?.failure_counts ?? {};
    return (Object.keys(counts) as FailureClass[]).filter((k) => (counts[k] ?? 0) > 0);
  }, [data]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 space-y-12">
      <section className="space-y-3">
        <h1
          className="text-3xl font-bold tracking-tight"
          style={{ color: "var(--foreground)" }}
        >
          Recall Lab
        </h1>
        <p
          className="text-base leading-relaxed max-w-3xl"
          style={{ color: "var(--muted)" }}
        >
          Retrieval-only view: did the strategy fetch a labelled supporting
          session inside the top-k result set, before the LLM judge ever sees
          the answer? HIT means the gold supporting session id appeared in the
          retrieved set; MISS means it did not. Cheaper to inspect than the
          full benchmark and useful for tuning top_k, embeddings, and store
          choice.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm" style={{ color: "var(--muted)" }}>
            Strategy
          </label>
          <select
            className="text-sm px-3 py-1.5 rounded border"
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            style={{
              borderColor: "var(--border)",
              background: "var(--card)",
              color: "var(--foreground)",
            }}
          >
            {availableStrategies.length === 0 && (
              <option value="">(loading…)</option>
            )}
            {availableStrategies.map((s) => (
              <option key={s} value={s}>
                {STRATEGY_LABELS[s as Strategy] ?? s}
              </option>
            ))}
          </select>
          {data?.top_k != null && (
            <span className="text-xs" style={{ color: "var(--muted)" }}>
              top_k = {data.top_k}
            </span>
          )}
          {data && (
            <span className="text-xs" style={{ color: "var(--muted)" }}>
              {counts.total} questions · {counts.hit} HIT · {counts.miss} MISS
              {counts.na > 0 ? ` · ${counts.na} N/A` : ""}
            </span>
          )}
        </div>
        {filterOptions.length > 0 && (
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm" style={{ color: "var(--muted)" }}>
              Failure
            </label>
            <select
              className="text-sm px-3 py-1.5 rounded border"
              value={failureFilter}
              onChange={(e) => setFailureFilter(e.target.value as FailureClass | "all")}
              style={{
                borderColor: "var(--border)",
                background: "var(--card)",
                color: "var(--foreground)",
              }}
            >
              <option value="all">All questions ({counts.total})</option>
              {filterOptions.map((k) => (
                <option key={k} value={k}>
                  {FAILURE_LABELS[k]} ({data?.failure_counts[k]})
                </option>
              ))}
            </select>
            {data?.judge_fail_threshold != null && (
              <span className="text-xs" style={{ color: "var(--muted)" }}>
                A judge score at or under {data.judge_fail_threshold} counts as a wrong answer.
              </span>
            )}
          </div>
        )}
        {strategy && STRATEGY_DESCRIPTIONS[strategy as Strategy] && (
          <p
            className="text-xs leading-relaxed max-w-3xl pt-1"
            style={{ color: "var(--muted)" }}
          >
            {STRATEGY_DESCRIPTIONS[strategy as Strategy]}
          </p>
        )}
      </section>

      {dataState?.state === "historical" && (
        <BenchmarkDataStatus state="historical" snapshot={dataState.snapshot} />
      )}

      {dataState?.state === "unavailable" ? (
        <BenchmarkDataStatus state="unavailable" message={dataState.message} />
      ) : (
        <>

      {measurable === false && (
        <section
          className="rounded-lg border p-4"
          style={{
            borderColor: "var(--border)",
            background: "var(--card)",
            color: "var(--muted)",
          }}
        >
          <p className="text-sm">
            Recall not measurable for this strategy. The strategy either
            doesn&apos;t expose a per-question retrieved-id list (e.g.
            full_context dumps every session by design) or wraps recall inside
            a vendor SDK that doesn&apos;t surface ranking. Accuracy and the
            other end-to-end axes are still on the Benchmark page.
          </p>
        </section>
      )}

      {loading && (
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Loading…
        </p>
      )}

      {notFound && !loading && (
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          No recall records on disk for {corpus}/{strategy}. Run{" "}
          <code style={{ color: "var(--foreground)" }}>
            memory-arena benchmark --corpus {corpus} --strategy {strategy}
          </code>{" "}
          first.
        </p>
      )}

      {data && data.records.length > 0 && (
        <section className="space-y-4">
          <h2
            className="text-xl font-semibold"
            style={{ color: "var(--foreground)" }}
          >
            {failureFilter === "all"
              ? "HIT / MISS by question"
              : `${FAILURE_LABELS[failureFilter]}: ${visibleRecords.length} of ${counts.total} questions`}
          </h2>
          <div className="space-y-3">
            {visibleRecords.map((rec) => {
              const v = verdict(rec, data.recall_at_k_measurable);
              const color =
                v === "HIT"
                  ? "var(--accent)"
                  : v === "MISS"
                    ? "var(--muted)"
                    : "var(--muted)";
              const stratColor =
                STRATEGY_COLORS[strategy as Strategy] ?? "var(--muted)";
              return (
                <div
                  key={rec.question_id}
                  className="rounded-lg border p-4 space-y-2"
                  style={{
                    borderColor:
                      v === "HIT" ? "var(--accent)" : "var(--border)",
                    background: "var(--card)",
                  }}
                >
                  <div className="flex items-baseline justify-between gap-3 flex-wrap">
                    <h3
                      className="text-sm font-mono"
                      style={{ color: "var(--foreground)" }}
                    >
                      <span
                        className="inline-block w-2 h-2 rounded-full mr-2 align-middle"
                        style={{ background: stratColor }}
                      />
                      {rec.question_id}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span
                        className="text-xs px-2 py-0.5 rounded"
                        style={{
                          background: "var(--background)",
                          color: "var(--muted)",
                          border: "1px solid var(--border)",
                        }}
                      >
                        {rec.category}
                      </span>
                      <span
                        className="text-xs font-semibold tabular-nums"
                        style={{ color }}
                      >
                        {v}
                      </span>
                    </div>
                  </div>
                  <div
                    className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs"
                    style={{ color: "var(--muted)" }}
                  >
                    <div className="space-y-1">
                      <div className="font-semibold uppercase tracking-wide opacity-70">
                        Retrieved
                      </div>
                      <div
                        className="font-mono leading-relaxed break-all"
                        style={{ color: "var(--foreground)" }}
                      >
                        {rec.supporting_session_ids?.length
                          ? rec.supporting_session_ids.join(", ")
                          : "(none)"}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="font-semibold uppercase tracking-wide opacity-70">
                        IR
                      </div>
                      <div
                        className="tabular-nums"
                        style={{ color: "var(--foreground)" }}
                      >
                        {rec.ir
                          ? `recall@${rec.ir.k} = ${(rec.ir.session_recall_at_k * 100).toFixed(0)}%, mrr = ${rec.ir.session_mrr.toFixed(2)}`
                          : "—"}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="font-semibold uppercase tracking-wide opacity-70">
                        Cost / latency
                      </div>
                      <div
                        className="tabular-nums"
                        style={{ color: "var(--foreground)" }}
                      >
                        {rec.cost_usd != null
                          ? `$${rec.cost_usd.toFixed(4)}`
                          : "—"}{" "}
                        · {fmtMs(rec.latency_ms)}
                      </div>
                    </div>
                  </div>
                  {rec.question && (
                    <details className="text-xs pt-1">
                      <summary
                        className="cursor-pointer select-none"
                        style={{ color: "var(--muted)" }}
                      >
                        {rec.failure_class
                          ? FAILURE_LABELS[rec.failure_class]
                          : "Evidence"}
                        {rec.judge_score != null
                          ? ` · judge ${rec.judge_score.toFixed(0)}/100`
                          : ""}
                      </summary>
                      <div
                        className="pt-3 space-y-3"
                        style={{ color: "var(--muted)" }}
                      >
                        <Field label="Question" value={rec.question} />
                        <Field
                          label="Expected answer"
                          value={rec.expected_answer ?? "(not in the question file)"}
                        />
                        <Field
                          label="Gold session"
                          value={
                            rec.gold_session_ids?.length
                              ? rec.gold_session_ids.join(", ")
                              : "(none labelled)"
                          }
                          mono
                        />
                        <Field
                          label="Retrieval"
                          value={`session ${rec.session_hit ? "hit" : "miss"}, turn ${
                            rec.turn_hit === null || rec.turn_hit === undefined
                              ? "not measured"
                              : rec.turn_hit
                                ? "hit"
                                : "miss"
                          }`}
                        />
                        <Field label="Answer given" value={rec.answer ?? "(none)"} />
                        {rec.score?.judge_rationale && (
                          <Field
                            label="Judge rationale (primary judge)"
                            value={rec.score.judge_rationale}
                          />
                        )}
                        <Field
                          label="Structural checks"
                          value={`${
                            rec.score?.structural_pass ? "pass" : "fail"
                          }, cited a labelled source: ${
                            rec.score?.sources_pass ? "yes" : "no"
                          }`}
                        />
                      </div>
                    </details>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}
        </>
      )}
    </div>
  );
}
