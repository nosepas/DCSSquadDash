import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { AircraftHint as Hint } from '../../api/types.aircraft';

/** Friendly banner explaining why no allied aircraft are shown. */
export function AircraftHint({ hint }: { hint: Hint | undefined }) {
  const { t } = useTranslation();
  if (hint === 'link_account') {
    return (
      <div className="notice" role="note">
        {t('aircraft.linkAccount')} <Link to="/profile">{t('aircraft.linkAction')}</Link>
      </div>
    );
  }
  if (hint === 'not_online') {
    return <div className="notice" role="note">{t('aircraft.notOnline')}</div>;
  }
  return null;
}
