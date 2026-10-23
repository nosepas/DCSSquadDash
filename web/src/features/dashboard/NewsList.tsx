import { useTranslation } from 'react-i18next';
import type { NewsItem } from '../../api/types';
import { Card } from '../../components/Card';
import { EmptyState } from '../../components/states/EmptyState';
import { formatTime } from '../../lib/format';

/** News arrive language-neutral (type + fields); the sentence comes from the i18n template `news.<type>`. */
function NewsLine({ item }: { item: NewsItem }) {
  const { t, i18n } = useTranslation();
  const known = i18n.exists(`news.${item.type}`);
  const text = known
    ? t(`news.${item.type}`, {
        coalition: item.coalition ? t(`coalition.${item.coalition}`) : '',
        zone: item.zone ?? '',
      })
    : t('news.unknown', { type: item.type });
  return (
    <li className={`news news-${item.coalition ?? 'neutral'}`}>
      <time dateTime={item.time_utc} className="mono muted small">{formatTime(item.time_utc, i18n.language)}</time>
      <span>
        {text}
        {item.actor && <span className="muted small"> · {t('news.by', { actor: item.actor })}</span>}
      </span>
    </li>
  );
}

export function NewsList({ items }: { items: NewsItem[] }) {
  const { t } = useTranslation();
  return (
    <Card title={t('dashboard.news')}>
      {items.length === 0 ? (
        <EmptyState message={t('dashboard.noNews')} />
      ) : (
        <ul className="feed">
          {items.map((n, i) => (
            <NewsLine key={`${n.time_utc}-${n.type}-${i}`} item={n} />
          ))}
        </ul>
      )}
    </Card>
  );
}
