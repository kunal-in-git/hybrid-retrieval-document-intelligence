import LatencyBreakdown from "@/components/LatencyBreakdown";
import RetrieverComparison from "@/components/RetrieverComparison";
import styles from "./PipelineInspector.module.css";

export default function PipelineInspector({ result }) {
  return (
    <details className={`card ${styles.inspector}`}>
      <summary className={styles.summary}>Under the hood</summary>

      <div className={styles.body}>
        <div>
          <h3 className={`section-title ${styles.subtitle}`}>Latency</h3>
          <LatencyBreakdown latency={result.latency} />
        </div>

        <div>
          <h3 className={`section-title ${styles.subtitle}`}>
            Retrieval stages (top 5)
          </h3>
          <p className={styles.hint}>
            Hover a result to highlight the same chunk in every stage. D / B / S
            = its rank in Dense / BM25 / Sparse.
          </p>
          <RetrieverComparison result={result} />
        </div>
      </div>
    </details>
  );
}
