import { useTranslation } from 'react-i18next';
import type { AdminServer } from '../../../api/types.admin';
import { Card } from '../../../components/Card';
import { useNow } from '../../../hooks/useNow';
import { relativeTime } from '../../../lib/time';
import { OnlineBadge } from '../OnlineBadge';
import { WarningList } from './WarningList';

/** Read-only connection status; the parent page refreshes `server` every ~10 s. */
export function StatusSection({ server }: { server: AdminServer }) {
  const { t, i18n } = useTranslation();
  const now = useNow(5000);
  const { agent } = server;
  const hasAgent = server.agents.some((a) => !a.revoked_at);
  return (
    <Card title={t('admin.server.status.title')}>
      <p className="muted section-intro">{t('admin.server.status.intro')}</p>
      <dl className="facts">
        <div><dt>{t('common.status')}</dt><dd><OnlineBadge online={server.online} /></dd></div>
        <div><dt>{t('admin.server.status.agentVersion')}</dt><dd className="mono">{agent.version ?? '–'}</dd></div>
        <div><dt>{t('admin.server.status.lastSeen')}</dt><dd>{relativeTime(agent.last_seen, now, i18n.language)}</dd></div>
        <div>
          <dt>{t('admin.server.status.queue')}</dt>
          <dd className="mono">{agent.queue_depth ?? '–'}</dd>
        </div>
      </dl>
      <p className="field-help">{t('admin.server.status.queueHelp')}</p>
      {!hasAgent && <p className="notice notice-warn">{t('admin.server.status.noAgent')}</p>}
      {agent.warnings.length > 0 ? (
        <WarningList warnings={agent.warnings} />
      ) : (
        hasAgent && <p className="notice" role="status">{t('admin.server.status.noWarnings')}</p>
      )}
    </Card>
  );
}
