import type { SnapshotInfo } from "@/lib/api";

type BenchmarkDataStatusProps =
  | { state: "historical"; snapshot: SnapshotInfo }
  | { state: "unavailable"; message: string };

export default function BenchmarkDataStatus(
  props: BenchmarkDataStatusProps
) {
  const historical = props.state === "historical";

  return (
    <section
      className="rounded-lg border p-4 space-y-1"
      style={{
        borderColor: "var(--border)",
        background: "var(--card)",
      }}
    >
      <h2 className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>
        {historical ? "Historical benchmark data" : "Benchmark data unavailable"}
      </h2>
      {historical ? (
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Snapshot {props.snapshot.snapshot_id}, protocol {props.snapshot.protocol_id},
          {" "}{props.snapshot.question_count} questions. This is historical data,
          not a current benchmark run.
        </p>
      ) : (
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          {props.message}
        </p>
      )}
    </section>
  );
}
