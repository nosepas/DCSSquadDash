import { useTranslation } from 'react-i18next';
import type { DtcModel, DtcPoint } from '../../api/types.dtc';
import { columnsFor } from '../../lib/dtc/listInfo';
import type { ListRef } from '../../lib/dtc/lists';
import { DecimalField } from './DecimalField';
import type { useDtcActions } from './useDtcActions';

type Actions = ReturnType<typeof useDtcActions>;

interface Props {
  model: DtcModel;
  list: ListRef;
  point: DtcPoint;
  index: number;
  count: number;
  approx: boolean;
  /** Server/live validation message for this point, if any. */
  problem?: string;
  actions: Actions;
}

const asNumber = (v: number | string | null): number | null => (typeof v === 'number' ? v : null);

/** One point of the active list: name/note, coordinates, elevation, aircraft-specific fields and row actions. */
export function PointCard({ model, list, point, index, count, approx, problem, actions }: Props) {
  const { t } = useTranslation();
  const id = `pt-${point.id ?? index}`;
  const cols = columnsFor(model, list);
  const text = (key: 'name' | 'note') => (
    <label key={key} className="dtc-text">
      <span className="dtc-num-label">{t(`dtc.fields.${key}`)}</span>
      <input type="text" value={point[key] ?? ''} placeholder={key === 'name' && model.aircraft === 'AH-64D_BLK_II' ? t('dtc.fields.autoName') : undefined}
        onChange={(e) => actions.patch(list, index, { [key]: e.target.value || undefined })} />
    </label>
  );
  const spd = point.extra?.spd;
  const tot = point.extra?.tot;
  return (
    <li className={`dtc-point${problem ? ' dtc-point-bad' : ''}`}>
      <div className="dtc-point-head">
        <b className="dtc-point-n">{index + 1}</b>
        <span className="dtc-point-actions">
          <button type="button" className="btn btn-ghost" disabled={index === 0} aria-label={t('dtc.points.up', { n: index + 1 })} onClick={() => actions.move(list, index, index - 1)}>▲</button>
          <button type="button" className="btn btn-ghost" disabled={index === count - 1} aria-label={t('dtc.points.down', { n: index + 1 })} onClick={() => actions.move(list, index, index + 1)}>▼</button>
          <button type="button" className="btn btn-ghost btn-danger" aria-label={t('dtc.points.deleteN', { n: index + 1 })} onClick={() => actions.remove(list, index)}>✕</button>
        </span>
      </div>
      {cols.includes('name') && text('name')}
      {cols.includes('note') && text('note')}
      <div className="dtc-coords">
        <DecimalField id={`${id}-lat`} label={t('dtc.fields.lat')} kind="lat" value={point.lat} onCommit={(v) => typeof v === 'number' && actions.patch(list, index, { lat: v })} />
        <DecimalField id={`${id}-lon`} label={t('dtc.fields.lon')} kind="lon" value={point.lon} onCommit={(v) => typeof v === 'number' && actions.patch(list, index, { lon: v })} />
        <DecimalField id={`${id}-el`} label={t('dtc.fields.elevation')} kind="elev" value={point.elevation_m} hint={approx ? t('dtc.fields.approx') : undefined}
          placeholder={t('dtc.fields.unknown')} onCommit={(v) => actions.patch(list, index, { elevation_m: asNumber(v) })} />
      </div>
      {cols.includes('spd') && (
        <div className="dtc-coords">
          <DecimalField id={`${id}-spd`} label={t('dtc.fields.speed')} kind="num" value={typeof spd === 'number' ? spd : null} onCommit={(v) => actions.extra(list, index, 'spd', asNumber(v) ?? 0)} />
          <DecimalField id={`${id}-tot`} label={t('dtc.fields.tot')} kind="time" value={typeof tot === 'string' ? tot : null} placeholder="HH:MM:SS" onCommit={(v) => actions.extra(list, index, 'tot', typeof v === 'string' ? v : '')} />
        </div>
      )}
      {problem && <p className="field-error" role="alert">{problem}</p>}
    </li>
  );
}
