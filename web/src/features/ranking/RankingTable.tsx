import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { RankingRow } from '../../api/types';
import { formatKd, formatNumber } from '../../lib/format';

/** Ranking rows; shared by the ranking page and the dashboard's top shooters. */
export function RankingTable({ rows, compact = false }: { rows: RankingRow[]; compact?: boolean }) {
  const { t, i18n } = useTranslation();
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th scope="col" className="num">{t('ranking.rank')}</th>
            <th scope="col">{t('ranking.pilot')}</th>
            <th scope="col" className="num">{t('ranking.kills')}</th>
            {!compact && <th scope="col" className="num">{t('ranking.deaths')}</th>}
            <th scope="col" className="num">{t('ranking.kd')}</th>
            {!compact && <th scope="col" className="num">{t('ranking.points')}</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.ucid}>
              <td className="num mono">{i + 1}</td>
              <th scope="row">
                <Link to={`/players/${r.ucid}`} className="mono">{r.name ?? r.ucid.slice(0, 8)}</Link>
              </th>
              <td className="num mono">{r.kills}</td>
              {!compact && <td className="num mono">{r.deaths}</td>}
              <td className="num mono">{formatKd(r.kd)}</td>
              {!compact && <td className="num mono">{formatNumber(r.points, i18n.language)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
