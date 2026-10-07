import DocumentsPanel from "@/components/DocumentsPanel";

const DocumentsPage = () => {
  return (
    <main className="container">
      <h1 className="page-title">Documents</h1>
      <p className="page-subtitle">
        Upload PDFs and follow each one through the ingestion pipeline.
      </p>
      <DocumentsPanel />
    </main>
  );
};

export default DocumentsPage;
