import { useState } from "react";
import styles from "./RetrieverComparison.module.css";

const COLUMNS = [
  { key: "dense_results", label: "Dense" },
  { key: "bm25_results", label: "BM25" },
  { key: "neural_sparse_results", label: "Neural sparse" },
  { key: "fused_results", label: "RRF fused" },
  { key: "reranked_results", label: "Reranked" },
];

const ROWS = 5;

function foundBy(item) {
  const parts = [];

  if (item.dense_rank) parts.push(`D${item.dense_rank}`);
  if (item.bm25_rank) parts.push(`B${item.bm25_rank}`);
  if (item.neural_sparse_rank) parts.push(`S${item.neural_sparse_rank}`);

  return parts.join(" ");
}

export default function RetrieverComparison({ result }) {
  const [hoveredChunkId, setHoveredChunkId] = useState(null);

  return (
    // On narrow screens the five columns scroll sideways inside this box
    <div className={styles.scroller}>
      <div
        className={styles.grid}
        style={{
          gridTemplateColumns: `repeat(${COLUMNS.length}, minmax(170px, 1fr))`,
        }}
      >
        {COLUMNS.map((column) => (
          <div key={column.key}>
            <h4 className={styles.columnTitle}>{column.label}</h4>

            {result[column.key].slice(0, ROWS).map((item, index) => (
              <div
                key={item.chunk_id}
                className={`${styles.item} ${
                  item.chunk_id === hoveredChunkId ? styles.hovered : ""
                }`}
                onMouseEnter={() => setHoveredChunkId(item.chunk_id)}
                onMouseLeave={() => setHoveredChunkId(null)}
              >
                <div className={styles.itemHeader}>
                  <span className={styles.rank}>#{index + 1}</span>
                  <span className={styles.file}>
                    {item.filename} · p.{item.page}
                  </span>
                </div>

                {foundBy(item) && (
                  <div className={styles.foundBy}>{foundBy(item)}</div>
                )}

                <div className={styles.snippet}>{item.text}</div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
