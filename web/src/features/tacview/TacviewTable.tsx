import { useTranslation } from 'react-i18next';
import type { TacviewHit } from '../../api/types.tacview';
import { CoalitionBadge } from '../../components/Coalition';
import { formatOffset, formatUtc } from '../../lib/tacview';

interface Props {
  hits: TacviewHit[];
  busyId: number | null;
  onDownload: (hit: TacviewHit) => void;
}

export function TacviewTable({ hits, busyId, onDownload }: Props) {
  const { t } = useTranslation();
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">{t('tacview.server')}</th>
            <th scope="col">{t('tacview.file')}</th>
            <th scope="col">{t('tacview.pilot')}</th>
            <th scope="col">{t('tacview.aircraft')}</th>
            <th scope="col">{t('tacview.utc')}</th>
            <th scope="col">{t('tacview.offset')}</th>
            <th scope="col"><span className="sr-only">{t('tacview.download')}</span></th>
          </tr>
        </thead>
        <tbody>
          {hits.map((h) => (
            <tr key={`${h.file_id}-${h.pilot}-${h.first_offset_s}`}>
              <td>{h.server_name}</td>
              <td className="mono wrap-anywhere">
                {h.file}
                {!h.complete && <span className="tag tag-warn" title={t('tacview.partialHint')}>{t('tacview.partial')}</span>}
              </td>
              <td>{h.pilot} <CoalitionBadge coalition={h.coalition} /></td>
              <td className="mono">{h.aircraft}</td>
              <td className="mono">{formatUtc(h.first_utc)} – {formatUtc(h.last_utc)}</td>
              <td className="mono">{formatOffset(h.first_offset_s)} – {formatOffset(h.last_offset_s)}</td>
              <td>
                <button type="button" className="btn" disabled={busyId !== null} aria-busy={busyId === h.file_id} onClick={() => onDownload(h)}>
                  {t('tacview.download')}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
