import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { readStored, writeStored } from '../lib/storage';
import ca from './ca.json';
import en from './en.json';
import es from './es.json';
import eu from './eu.json';
import gl from './gl.json';

export const LANGUAGES = [
  { code: 'es', label: 'Español' },
  { code: 'ca', label: 'Català' },
  { code: 'en', label: 'English' },
  { code: 'gl', label: 'Galego' },
  { code: 'eu', label: 'Euskara' },
] as const;

export type LanguageCode = (typeof LANGUAGES)[number]['code'];
export const DEFAULT_LANGUAGE: LanguageCode = 'es';
const STORAGE_KEY = 'fox3.lang';

export function isLanguage(code: string | null): code is LanguageCode {
  return LANGUAGES.some((l) => l.code === code);
}

function initialLanguage(): LanguageCode {
  const stored = readStored(STORAGE_KEY);
  return isLanguage(stored) ? stored : DEFAULT_LANGUAGE;
}

export function setLanguage(code: LanguageCode): void {
  writeStored(STORAGE_KEY, code);
  void i18n.changeLanguage(code);
}

void i18n.use(initReactI18next).init({
  resources: {
    es: { translation: es },
    ca: { translation: ca },
    en: { translation: en },
    gl: { translation: gl },
    eu: { translation: eu },
  },
  lng: initialLanguage(),
  fallbackLng: DEFAULT_LANGUAGE,
  interpolation: { escapeValue: false },
});

i18n.on('languageChanged', (lng) => {
  document.documentElement.lang = lng;
});
document.documentElement.lang = i18n.language;

export default i18n;
