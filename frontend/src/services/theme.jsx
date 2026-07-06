/**
 * Theme Context - Dark/Light Mode Support
 */

import { useState, useCallback, useEffect, createContext, useContext } from 'react';

export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
};

export const THEME_STORAGE_KEY = 'adas-theme-preference';

const ThemeContext = createContext({
  theme: THEMES.LIGHT,
  isDark: false,
  setTheme: () => {},
  toggleTheme: () => {},
});

function getSystemTheme() {
  if (typeof window === 'undefined') return THEMES.LIGHT;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? THEMES.DARK : THEMES.LIGHT;
}

function resolveTheme(themePreference) {
  if (themePreference === THEMES.SYSTEM) {
    return getSystemTheme();
  }
  return themePreference;
}

function applyTheme(theme) {
  const resolved = resolveTheme(theme);
  const isDark = resolved === THEMES.DARK;

  document.documentElement.setAttribute('data-theme', resolved);
  document.documentElement.classList.toggle('dark', isDark);
  document.documentElement.classList.toggle('light', !isDark);

  // Update meta theme-color
  let metaTheme = document.querySelector('meta[name="theme-color"]');
  if (!metaTheme) {
    metaTheme = document.createElement('meta');
    metaTheme.name = 'theme-color';
    document.head.appendChild(metaTheme);
  }
  metaTheme.content = isDark ? '#1a1a2e' : '#f8fafc';
}

export function ThemeProvider({ children, initialTheme }) {
  // Load saved preference or use initial
  const [theme, setThemeState] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(THEME_STORAGE_KEY);
      if (saved && Object.values(THEMES).includes(saved)) {
        return saved;
      }
    }
    return initialTheme || THEMES.LIGHT;
  });

  const isDark = resolveTheme(theme) === THEMES.DARK;

  const setTheme = useCallback((newTheme) => {
    if (!Object.values(THEMES).includes(newTheme)) {
      console.warn(`Invalid theme: ${newTheme}`);
      return;
    }
    setThemeState(newTheme);
    localStorage.setItem(THEME_STORAGE_KEY, newTheme);
    applyTheme(newTheme);
  }, []);

  const toggleTheme = useCallback(() => {
    const currentResolved = resolveTheme(theme);
    const newTheme = currentResolved === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK;
    setTheme(newTheme);
  }, [theme, setTheme]);

  // Apply theme on mount and theme change
  useEffect(() => {
    applyTheme(theme);

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === THEMES.SYSTEM) {
        applyTheme(THEMES.SYSTEM);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  const value = {
    theme,
    isDark,
    setTheme,
    toggleTheme,
    themes: THEMES,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    // Return defaults if not in provider
    return {
      theme: THEMES.LIGHT,
      isDark: false,
      setTheme: () => {},
      toggleTheme: () => {},
      themes: THEMES,
    };
  }
  return context;
}

export default { ThemeProvider, useTheme, THEMES };
