import { api } from "../api";

export async function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/upload/", form);
  return data.url;
}

export function uploadErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.join(", ");
  if (error?.response?.status === 413) return "File is too large (max 50 MB)";
  if (error?.response?.status === 401) return "Session expired — sign in again";
  return "Upload failed — check your connection and try again";
}
