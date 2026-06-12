import axios from "axios";
import { clearAccessToken, getAccessToken, setAccessToken } from "./lib/auth";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

let isRefreshing = false;
let queue = [];

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

const refreshClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

async function refreshAccessToken() {
  const { data } = await refreshClient.post("/auth/refresh/");
  setAccessToken(data.access);
  return data.access;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }
    originalRequest._retry = true;

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push({ resolve, reject });
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return api(originalRequest);
      });
    }

    isRefreshing = true;
    try {
      const token = await refreshAccessToken();
      queue.forEach((p) => p.resolve(token));
      queue = [];
      originalRequest.headers.Authorization = `Bearer ${token}`;
      return api(originalRequest);
    } catch (refreshErr) {
      queue.forEach((p) => p.reject(refreshErr));
      queue = [];
      clearAccessToken();
      return Promise.reject(refreshErr);
    } finally {
      isRefreshing = false;
    }
  }
);

export { refreshAccessToken };
