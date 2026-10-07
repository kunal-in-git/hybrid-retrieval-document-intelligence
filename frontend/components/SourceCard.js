import { useState } from "react";

export default function SourceCard({ context, number, active }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article
      id={`source-${number}`}
      style={{
        border: active ? "2px solid #2563eb" : "1px solid #ccc",
        padding: "12px",
        marginTop: "12px",
      }}
    >
      <p>
        <strong>
          [{number}] {context.filename}
        </strong>{" "}
        · page {context.page}
        {context.section && <> · {context.section}</>}
      </p>

      <p style={{ whiteSpace: "pre-wrap" }}>
        {expanded ? context.parent_text : context.matched_child_text}
      </p>

      {context.parent_text !== context.matched_child_text && (
        <button type="button" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show matched passage" : "Show full context"}
        </button>
      )}
    </article>
  );
}
