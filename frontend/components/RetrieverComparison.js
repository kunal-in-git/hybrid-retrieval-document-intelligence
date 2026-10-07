import { useState } from "react";

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
    <div
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${COLUMNS.length}, 1fr)`,
        gap: "8px",
      }}
    >
      {COLUMNS.map((column) => (
        <div key={column.key}>
          <h4>{column.label}</h4>

          {result[column.key].slice(0, ROWS).map((item, index) => (
            <div
              key={item.chunk_id}
              onMouseEnter={() => setHoveredChunkId(item.chunk_id)}
              onMouseLeave={() => setHoveredChunkId(null)}
              style={{
                border: "1px solid #ccc",
                padding: "6px",
                marginBottom: "6px",
                fontSize: "12px",
                background:
                  item.chunk_id === hoveredChunkId
                    ? "rgba(37, 99, 235, 0.25)"
                    : "transparent",
              }}
            >
              <strong>#{index + 1}</strong> {item.filename} · p.{item.page}
              {foundBy(item) && <div>found by: {foundBy(item)}</div>}
              <div>{item.text.slice(0, 80)}</div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
