"use client";

import { useEffect, useState } from "react";
import { getDocuments, uploadDocument } from "@/lib/api";

const IN_PROGRESS = ["QUEUED", "PARSING", "CHUNKING", "EMBEDDING", "INDEXING"];

const STATUS_LABELS = {
  QUEUED: "Queued",
  PARSING: "Parsing",
  CHUNKING: "Chunking",
  EMBEDDING: "Embedding",
  INDEXING: "Indexing",
  COMPLETED: "Ready",
  FAILED: "Failed",
};

const POLL_INTERVAL_MS = 2000;

export default function DocumentsPanel() {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  // -------------------------------------------------
  // 1. Load all documents once, when the page opens
  // -------------------------------------------------
  useEffect(() => {
    async function load() {
      try {
        setDocuments(await getDocuments());
      } catch (err) {
        setError(err.message);
      }
    }

    load();
  }, []);

  // -------------------------------------------------
  // 2. Poll only the documents still being processed
  // -------------------------------------------------
  useEffect(() => {
    const processingIds = documents
      .filter((doc) => IN_PROGRESS.includes(doc.status))
      .map((doc) => doc.document_id);

    if (processingIds.length === 0) {
      return;
    }

    const timer = setInterval(async () => {
      try {
        const updates = await getDocuments(processingIds);

        setDocuments((current) =>
          current.map(
            (doc) =>
              updates.find((u) => u.document_id === doc.document_id) || doc
          )
        );
      } catch {
        // Ignore a failed poll; the next tick tries again.
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [documents]);

  // -------------------------------------------------
  // 3. Upload as soon as a file is picked
  // -------------------------------------------------
  async function handleFileChange(event) {
    const input = event.target;
    const file = input.files[0];

    if (!file) {
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await uploadDocument(file);
      setDocuments(await getDocuments());
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setUploading(false);
      input.value = "";
    }
  }

  return (
    <section>
      <label>
        Upload PDF:{" "}
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          disabled={uploading}
        />
      </label>
      {uploading && <p>Uploading...</p>}
      {error && <p>Error: {error}</p>}

      <table>
        <thead>
          <tr>
            <th>File</th>
            <th>Status</th>
            <th>Uploaded</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.document_id}>
              <td>{doc.filename}</td>
              <td>
                {STATUS_LABELS[doc.status] || doc.status}
                {IN_PROGRESS.includes(doc.status) && " ..."}
                {doc.error_message && <div>{doc.error_message}</div>}
              </td>
              <td>{new Date(doc.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
