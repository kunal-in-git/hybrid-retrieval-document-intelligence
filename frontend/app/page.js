import AskPanel from "@/components/AskPanel";

export default function Home() {
  return (
    <main className="container">
      <h1 className="page-title">Ask your documents</h1>
      <p className="page-subtitle">
        Dense + BM25 + neural sparse retrieval, fused with RRF, reranked by a
        cross-encoder, answered by Llama 3.1 with citations.
      </p>
      <AskPanel />
    </main>
  );
}
