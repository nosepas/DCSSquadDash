import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { searchPlayers } from '../../api/players';
import { Card, PageHeader } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { useDebounce } from '../../hooks/useDebounce';
import { formatDateTime } from '../../lib/format';

const MIN_CHARS = 2;

function SearchResults({ term }: { term: string }) {
  const { t, i18n } = useTranslation();
  const state = useAsync((signal) => searchPlayers(term, signal), [term]);
  return (
    <AsyncView state={state} isEmpty={(d) => d.length === 0} emptyMessage={t('players.noResults')}>
      {(hits) => (
        <ul className="list">
          {hits.map((p) => (
            <li key={p.ucid}>
              <Link to={`/players/${p.ucid}`} className="mono">{p.last_name}</Link>
              <span className="muted small">
                {t('players.lastSeen')}: {formatDateTime(p.last_seen_at, i18n.language)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </AsyncView>
  );
}

export default function PlayersPage() {
  const { t } = useTranslation();
  const [text, setText] = useState('');
  const term = useDebounce(text.trim(), 350);
  return (
    <>
      <PageHeader title={t('players.title')} />
      <Card>
        <label className="field">
          <span>{t('players.search')}</span>
          <input type="search" value={text} placeholder={t('players.placeholder')} onChange={(e) => setText(e.target.value)} autoComplete="off" />
        </label>
        {term.length >= MIN_CHARS ? <SearchResults term={term} /> : <p className="muted">{t('players.minChars')}</p>}
      </Card>
    </>
  );
}
