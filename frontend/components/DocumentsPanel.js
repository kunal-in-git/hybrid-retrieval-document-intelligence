"use client";

import { useEffect, useState } from "react";
import { getDocuments, uploadDocument } from "@/lib/api";
import styles from "./DocumentsPanel.module.css";

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

function badgeClass(status) {
  if (status === "COMPLETED") return styles.ready;
  if (status === "FAILED") return styles.failed;
  return styles.progress;
}

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

  const processingCount = documents.filter((doc) =>
    IN_PROGRESS.includes(doc.status)
  ).length;

  return (
    <section>
      <div className={styles.toolbar}>
        <span className={styles.count}>
          {documents.length} documents
          {processingCount > 0 && ` · ${processingCount} processing`}
        </span>

        {/* The label looks like a button; clicking it opens the hidden file input */}
        <label
          className={`btn ${styles.upload} ${uploading ? styles.disabled : ""}`}
        >
          {uploading ? "Uploading..." : "Upload PDF"}
          <input
            className={styles.fileInput}
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            disabled={uploading}
          />
        </label>
      </div>

      {error && <p className="error">Error: {error}</p>}

      <div className={`card ${styles.tableWrap}`}>
        <table className={styles.table}>
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
                <td className={styles.filename}>{doc.filename}</td>
                <td>
                  <span className={`${styles.badge} ${badgeClass(doc.status)}`}>
                    {IN_PROGRESS.includes(doc.status) && (
                      <span className={styles.pulse} />
                    )}
                    {STATUS_LABELS[doc.status] || doc.status}
                  </span>
                  {doc.error_message && (
                    <div className={styles.errorMessage}>
                      {doc.error_message}
                    </div>
                  )}
                </td>
                <td className={styles.date}>
                  {new Date(doc.created_at).toLocaleString()}
                </td>
              </tr>
            ))}

            {documents.length === 0 && (
              <tr>
                <td colSpan={3} className={styles.empty}>
                  No documents yet. Upload a PDF to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
