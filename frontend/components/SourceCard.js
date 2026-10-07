import { useState } from "react";
import styles from "./SourceCard.module.css";

export default function SourceCard({ context, number, active }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article
      id={`source-${number}`}
      className={`card ${styles.source} ${active ? styles.active : ""}`}
    >
      <div className={styles.header}>
        <span className={styles.number}>{number}</span>
        <span className={styles.filename}>{context.filename}</span>
        <span className={styles.meta}>page {context.page}</span>
        {context.section && (
          <span className={styles.section}>{context.section}</span>
        )}
        {context.rerank_score != null && (
          <span className={styles.score} title="Cross-encoder rerank score">
            rerank {context.rerank_score.toFixed(2)}
          </span>
        )}
      </div>

      <p className={styles.text}>
        {expanded ? context.parent_text : context.matched_child_text}
      </p>

      {context.parent_text !== context.matched_child_text && (
        <button
          type="button"
          className={`btn-link ${styles.toggle}`}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Show matched passage" : "Show full context"}
        </button>
      )}
    </article>
  );
}
