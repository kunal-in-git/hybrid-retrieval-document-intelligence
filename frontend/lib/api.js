import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  paramsSerializer: { indexes: null },
});

export async function getHealth() {
  const response = await api.get("/health");
  return response.data;
}

export async function askQuestion(query) {
  const response = await api.get("/search/hybrid", {
    params: { query: query, top_k: 10 },
  });
  return response.data;
}

export async function getDocuments(documentIds) {
  const response = await api.get("/documents", {
    params: { document_ids: documentIds },
  });
  return response.data.documents;
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/documents", formData);
  return response.data;
}
