import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { searchTacview } from '../../api/tacview';
import { Card, PageHeader } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { useDebounce } from '../../hooks/useDebounce';
import { useServers } from '../servers/ServerContext';
import { DownloadStatus } from './DownloadStatus';
import { TacviewTable } from './TacviewTable';
import { useTacviewDownload } from './useTacviewDownload';

const MIN_CHARS = 2;

function Results({ term, serverId }: { term: string; serverId: string | undefined }) {
  const { t } = useTranslation();
  const state = useAsync((signal) => searchTacview(term, serverId, signal), [term, serverId]);
  const download = useTacviewDownload();
  return (
    <>
      <DownloadStatus state={download.state} onCancel={download.cancel} />
      <AsyncView state={state} isEmpty={(d) => d.length === 0} emptyMessage={t('tacview.noResults')}>
        {(hits) => <TacviewTable hits={hits} busyId={download.state.phase === 'idle' ? null : download.state.fileId} onDownload={(h) => void download.start(h)} />}
      </AsyncView>
    </>
  );
}

export default function TacviewPage() {
  const { t } = useTranslation();
  const servers = useServers().list.data ?? [];
  const [text, setText] = useState('');
  const [serverId, setServerId] = useState('');
  const term = useDebounce(text.trim(), 350);
  return (
    <>
      <PageHeader title={t('tacview.title')} />
      <Card>
        <p className="muted">{t('tacview.intro')}</p>
        <div className="filters">
          <label className="field grow">
            <span>{t('tacview.search')}</span>
            <input type="search" value={text} placeholder={t('tacview.placeholder')} onChange={(e) => setText(e.target.value)} autoComplete="off" />
          </label>
          <label className="field">
            <span>{t('tacview.server')}</span>
            <select value={serverId} onChange={(e) => setServerId(e.target.value)}>
              <option value="">{t('common.all')}</option>
              {servers.map((s) => (
                <option key={s.server_id} value={s.server_id}>{s.name}</option>
              ))}
            </select>
          </label>
        </div>
        {term.length >= MIN_CHARS ? <Results term={term} serverId={serverId || undefined} /> : <p className="muted">{t('tacview.minChars')}</p>}
      </Card>
    </>
  );
}
