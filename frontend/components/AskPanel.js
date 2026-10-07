"use client";

import AnswerText from "@/components/AnswerText";
import SourceCard from "@/components/SourceCard";

import { useState } from "react";
import { askQuestion } from "@/lib/api";
import PipelineInspector from "@/components/PipelineInspector";

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
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask a question about your documents..."
        />
        <button type="submit" disabled={loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {error && <p>Error: {error}</p>}

      {result && (
        <div>
          <h2>Answer</h2>
          <AnswerText
            answer={result.answer}
            sourceCount={result.contexts.length}
            onCitationClick={handleCitationClick}
          />
          <p>Answered in {(result.latency.total_ms / 1000).toFixed(1)}s</p>

          <h2>Sources</h2>
          {result.contexts.map((context, index) => (
            <SourceCard
              key={context.parent_id}
              context={context}
              number={index + 1}
              active={activeSource === index + 1}
            />
          ))}
          <PipelineInspector result={result} />
        </div>
      )}

    </section>
  );
}
