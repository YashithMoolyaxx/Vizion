import { create } from "zustand";
import { api, refreshAccessToken } from "../api";
import { clearAccessToken, getAccessToken, setAccessToken } from "../lib/auth";

export const useAuthStore = create((set) => ({
  user: null,
  session: null,
  loading: true,

  login: async (username, password) => {
    const { data } = await api.post("/auth/login/", { username, password });
    setAccessToken(data.access);
    const [me, session] = await Promise.all([
      api.get("/auth/me/"),
      api.get("/auth/session/"),
    ]);
    set({ user: me.data, session: session.data });
    return me.data;
  },

  register: async (username, email, password) => {
    await api.post("/auth/register/", { username, email, password });
    return useAuthStore.getState().login(username, password);
  },

  logout: async () => {
    try {
      await api.post("/auth/logout/");
    } catch {
      /* ignore */
    }
    clearAccessToken();
    set({ user: null, session: null });
  },

  fetchMe: async () => {
    try {
      if (!getAccessToken()) {
        try {
          await refreshAccessToken();
        } catch {
          set({ user: null, session: null, loading: false });
          return null;
        }
      }
      const { data } = await api.get("/auth/me/");
      let session = null;
      try {
        const s = await api.get("/auth/session/");
        session = s.data;
      } catch {
        session = null;
      }
      set({ user: data, session, loading: false });
      return data;
    } catch {
      clearAccessToken();
      set({ user: null, session: null, loading: false });
      return null;
    }
  },
}));
