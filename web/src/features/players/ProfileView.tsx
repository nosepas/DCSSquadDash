import { useTranslation } from 'react-i18next';
import type { Profile } from '../../api/types';
import { Card } from '../../components/Card';
import { EmptyState } from '../../components/states/EmptyState';
import { formatDateTime, formatKd, formatNumber, kdRatio } from '../../lib/format';

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat">
      <dt>{label}</dt>
      <dd className="mono">{value}</dd>
    </div>
  );
}

export function ProfileView({ profile }: { profile: Profile }) {
  const { t, i18n } = useTranslation();
  return (
    <>
      <Card>
        <h2 className="profile-name mono">{profile.name}</h2>
        <p className="muted small mono">{profile.ucid}</p>
        <p>
          <span className={`tag ${profile.discord_linked ? 'tag-ok' : ''}`}>
            {profile.discord_linked ? t('profile.discordLinked') : t('profile.discordNotLinked')}
          </span>
        </p>
        <dl className="facts">
          <div>
            <dt>{t('profile.firstSeen')}</dt>
            <dd className="mono">{formatDateTime(profile.first_seen_at, i18n.language)}</dd>
          </div>
          <div>
            <dt>{t('profile.lastSeen')}</dt>
            <dd className="mono">{formatDateTime(profile.last_seen_at, i18n.language)}</dd>
          </div>
        </dl>
      </Card>
      <h2 className="section-title">{t('profile.serverStats')}</h2>
      {profile.servers.length === 0 ? (
        <EmptyState message={t('profile.noStats')} />
      ) : (
        <div className="grid grid-cards">
          {profile.servers.map((s) => (
            <Card key={s.server_id} title={s.server_name ?? s.server_id}>
              <dl className="stats">
                <Stat label={t('ranking.kills')} value={s.kills} />
                <Stat label={t('ranking.deaths')} value={s.deaths} />
                <Stat label={t('ranking.kd')} value={formatKd(kdRatio(s.kills, s.deaths))} />
                <Stat label={t('ranking.points')} value={formatNumber(s.points, i18n.language)} />
              </dl>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}
