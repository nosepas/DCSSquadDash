import { useTranslation } from 'react-i18next';
import { isLanguage, LANGUAGES, setLanguage } from '../../i18n';

export function LanguageSelect() {
  const { t, i18n } = useTranslation();
  return (
    <label className="select-field">
      <span className="sr-only">{t('header.language')}</span>
      <select
        value={i18n.language}
        onChange={(e) => {
          if (isLanguage(e.target.value)) setLanguage(e.target.value);
        }}
      >
        {LANGUAGES.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>
    </label>
  );
}
