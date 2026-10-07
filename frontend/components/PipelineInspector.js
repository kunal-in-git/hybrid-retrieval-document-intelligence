import LatencyBreakdown from "@/components/LatencyBreakdown";
import RetrieverComparison from "@/components/RetrieverComparison";

export default function PipelineInspector({ result }) {
  return (
    <details>
      <summary>Under the hood</summary>

      <h3>Latency</h3>
      <LatencyBreakdown latency={result.latency} />

      <h3>Retrieval stages (top {5})</h3>
      <RetrieverComparison result={result} />
    </details>
  );
}
