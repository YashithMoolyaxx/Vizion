import { create } from "zustand";

export const useThemeStore = create((set) => ({
  dark: localStorage.getItem("theme") !== "light",
  toggle: () =>
    set((state) => {
      const next = !state.dark;
      localStorage.setItem("theme", next ? "dark" : "light");
      return { dark: next };
    })
}));
