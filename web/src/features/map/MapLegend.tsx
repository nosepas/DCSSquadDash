import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

/** Zone/connection legend; `children` are extra <li> entries (e.g. the aircraft layer controls). */
export function MapLegend({ children }: { children?: ReactNode }) {
  const { t } = useTranslation();
  return (
    <ul className="legend" aria-label={t('map.legend')}>
      {(['red', 'blue', 'neutral'] as const).map((c) => (
        <li key={c}>
          <span className={`zone-dot zone-${c} static`} aria-hidden="true" />
          {t(`coalition.${c}`)}
        </li>
      ))}
      <li>
        <span className="zone-dot zone-neutral hq static" aria-hidden="true" />
        {t('map.hq')}
      </li>
      <li>
        <span className="zone-dot zone-neutral at-risk static" aria-hidden="true" />
        {t('map.atRisk')}
      </li>
      <li>
        <span className="legend-line front" aria-hidden="true" />
        {t('map.front')}
      </li>
      <li>
        <span className="legend-line" aria-hidden="true" />
        {t('map.link')}
      </li>
      {children}
    </ul>
  );
}
