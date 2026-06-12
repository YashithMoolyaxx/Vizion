import { create } from "zustand";
import { applyTheme, getStoredTheme, saveTheme } from "../lib/theme";

export const useThemeStore = create((set, get) => ({
  theme: getStoredTheme(),

  setTheme: (theme) => {
    const nextTheme = theme === "dark" ? "dark" : "light";
    saveTheme(nextTheme);
    applyTheme(nextTheme);
    set({ theme: nextTheme });
  },

  toggleTheme: () => {
    const nextTheme = get().theme === "dark" ? "light" : "dark";
    get().setTheme(nextTheme);
  },
}));
