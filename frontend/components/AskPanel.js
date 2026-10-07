"use client";

import { useState } from "react";
import { askQuestion } from "@/lib/api";
import AnswerText from "@/components/AnswerText";
import SourceCard from "@/components/SourceCard";
import PipelineInspector from "@/components/PipelineInspector";
import styles from "./AskPanel.module.css";

export default function AskPanel() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeSource, setActiveSource] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!query.trim()) {
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setActiveSource(null);

    try {
      const data = await askQuestion(query);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleCitationClick(number) {
    setActiveSource(number);

    document
      .getElementById(`source-${number}`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  return (
    <section>
      <form className={styles.form} onSubmit={handleSubmit}>
        <input
          className="input"
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask a question about your documents..."
        />
        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {error && <p className="error">Error: {error}</p>}

      {loading && (
        <div className={`card ${styles.loading}`}>
          <span className={styles.spinner} />
          Retrieving with three retrievers and generating an answer. This
          usually takes around 10 seconds.
        </div>
      )}

      {result && (
        <>
          <div className={`card ${styles.answer}`}>
            <div className={styles.answerHeader}>
              <h2 className="section-title">Answer</h2>
              <span className={styles.meta}>
                {(result.latency.total_ms / 1000).toFixed(1)} s ·{" "}
                {result.contexts.length} sources
              </span>
            </div>

            <AnswerText
              answer={result.answer}
              sourceCount={result.contexts.length}
              onCitationClick={handleCitationClick}
            />
          </div>

          <h2 className={`section-title ${styles.sourcesTitle}`}>Sources</h2>
          <div className={styles.sources}>
            {result.contexts.map((context, index) => (
              <SourceCard
                key={context.parent_id}
                context={context}
                number={index + 1}
                active={activeSource === index + 1}
              />
            ))}
          </div>

          <PipelineInspector result={result} />
        </>
      )}
    </section>
  );
}
