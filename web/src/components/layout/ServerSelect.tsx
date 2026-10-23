import { useTranslation } from 'react-i18next';
import { useServers } from '../../features/servers/ServerContext';

export function ServerSelect() {
  const { t } = useTranslation();
  const { list, current, select } = useServers();
  const servers = list.data ?? [];
  if (servers.length === 0) return <span className="muted small">{t('header.noServers')}</span>;
  return (
    <label className="select-field">
      <span className="sr-only">{t('header.server')}</span>
      <select value={current?.server_id ?? ''} onChange={(e) => select(e.target.value)}>
        {servers.map((s) => (
          <option key={s.server_id} value={s.server_id}>
            {s.online ? '● ' : '○ '}
            {s.name}
            {s.online ? '' : ` (${t('header.offline')})`}
          </option>
        ))}
      </select>
    </label>
  );
}
