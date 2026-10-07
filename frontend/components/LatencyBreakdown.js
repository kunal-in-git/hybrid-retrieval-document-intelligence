import styles from "./LatencyBreakdown.module.css";

const STAGES = [
  { key: "dense_ms", label: "Dense (pgvector)" },
  { key: "bm25_ms", label: "BM25" },
  { key: "neural_sparse_ms", label: "Neural sparse" },
  { key: "rrf_ms", label: "RRF fusion" },
  { key: "rerank_ms", label: "Cross-encoder rerank" },
  { key: "parent_ms", label: "Parent expansion" },
  { key: "answer_ms", label: "LLM answer", generation: true },
];

export default function LatencyBreakdown({ latency }) {
  return (
    <div>
      {STAGES.map((stage) => {
        const ms = latency[stage.key];
        const percent = (ms / latency.total_ms) * 100;

        return (
          <div key={stage.key} className={styles.row}>
            <span>{stage.label}</span>

            <div className={styles.track}>
              {/* Width depends on data, so it stays an inline style */}
              <div
                className={`${styles.bar} ${stage.generation ? styles.generation : ""}`}
                style={{ width: `${percent}%` }}
              />
            </div>

            <span className={styles.value}>{ms.toFixed(0)} ms</span>
          </div>
        );
      })}

      <p className={styles.total}>
        Total {(latency.total_ms / 1000).toFixed(1)} s · retrieval{" "}
        {latency.retrieval_total_ms.toFixed(0)} ms · generation{" "}
        {latency.answer_ms.toFixed(0)} ms
      </p>
    </div>
  );
}
