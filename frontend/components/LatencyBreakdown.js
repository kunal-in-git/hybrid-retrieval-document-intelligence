const STAGES = [
  { key: "dense_ms", label: "Dense (pgvector)" },
  { key: "bm25_ms", label: "BM25" },
  { key: "neural_sparse_ms", label: "Neural sparse" },
  { key: "rrf_ms", label: "RRF fusion" },
  { key: "rerank_ms", label: "Cross-encoder rerank" },
  { key: "parent_ms", label: "Parent expansion" },
  { key: "answer_ms", label: "LLM answer" },
];

export default function LatencyBreakdown({ latency }) {
  return (
    <div>
      {STAGES.map((stage) => {
        const ms = latency[stage.key];
        const percent = (ms / latency.total_ms) * 100;

        return (
          <div key={stage.key} style={{ marginBottom: "6px" }}>
            <div>
              {stage.label}: {ms.toFixed(0)} ms
            </div>
            <div
              style={{
                background: "#2563eb",
                height: "8px",
                width: `${percent}%`,
                minWidth: "2px",
              }}
            />
          </div>
        );
      })}

      <p>
        Total: {(latency.total_ms / 1000).toFixed(1)} s (retrieval{" "}
        {latency.retrieval_total_ms.toFixed(0)} ms)
      </p>
    </div>
  );
}
