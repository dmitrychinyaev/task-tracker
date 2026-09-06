import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { ru, en } from './translations';

export type Lang = 'ru' | 'en';

const messages: Record<Lang, Record<string, string>> = { ru, en };

type I18nContextValue = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
};

const I18nContext = createContext<I18nContextValue>({
  lang: 'ru',
  setLang: () => undefined,
  t: (k: string) => k,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    const stored = localStorage.getItem('lang');
    return stored === 'en' ? 'en' : 'ru';
  });

  const setLang = (l: Lang) => {
    setLangState(l);
    localStorage.setItem('lang', l);
  };

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const t = (key: string): string => messages[lang][key] ?? messages.en[key] ?? key;

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}

export function statusLabel(lang: Lang, status: string): string {
  return messages[lang][`status.${status}`] ?? status;
}

export function priorityLabel(lang: Lang, priority: string): string {
  return messages[lang][`priority.${priority}`] ?? priority;
}

export function sprintStatusLabel(lang: Lang, status: string): string {
  return messages[lang][`sprint.status.${status}`] ?? status;
}
