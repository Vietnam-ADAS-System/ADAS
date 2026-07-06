/**
 * i18n Service - Lightweight version
 */
import { useState, useCallback, createContext, useContext } from 'react';
import { translations } from './translations.js';

export const LANGUAGES = { VI: 'vi', EN: 'en', ZH: 'zh' };
export const LANGUAGE_NAMES = {
  [LANGUAGES.VI]: 'Tiếng Việt',
  [LANGUAGES.EN]: 'English',
  [LANGUAGES.ZH]: '中文',
};

const I18nContext = createContext(null);

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error('useI18n must be used within I18nProvider');

  const { language, setLanguage, t, languages, languageNames } = context;
  return { language, setLanguage, t, languages, languageNames };
}

export function I18nProvider({ children, initialLanguage = LANGUAGES.VI }) {
  const [language, setLanguage] = useState(initialLanguage);

  const t = useCallback((key) => {
    return translations[language]?.[key] || translations['en']?.[key] || key;
  }, [language]);

  return (
    <I18nContext.Provider value={{ language, setLanguage, t, languages: LANGUAGES, languageNames: LANGUAGE_NAMES }}>
      {children}
    </I18nContext.Provider>
  );
}
