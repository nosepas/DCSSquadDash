import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { DtcModel } from '../../api/types.dtc';
import type { ServerIssue } from '../../lib/dtc/errorDetails';
import { getPoints, type ListRef } from '../../lib/dtc/lists';
import { DecimalField } from './DecimalField';
import { PointCard } from './PointCard';
import type { useDtcActions } from './useDtcActions';

type Actions = ReturnType<typeof useDtcActions>;

interface Props {
  model: DtcModel;
  list: ListRef;
  approx: Record<string, true>;
  serverIssues: ServerIssue[];
  actions: Actions;
}

function AddByCoords({ disabled, onAdd }: { disabled: boolean; onAdd: (lat: number, lon: number) => void }) {
  const { t } = useTranslation();
  const [lat, setLat] = useState<number | null>(null);
  const [lon, setLon] = useState<number | null>(null);
  const [round, setRound] = useState(0);  // remounts the inputs to clear them after adding
  const ready = lat !== null && lon !== null;
  return (
    <div className="dtc-add" key={round}>
      <DecimalField id="dtc-add-lat" label={t('dtc.fields.lat')} kind="lat" value={lat} onCommit={(v) => setLat(typeof v === 'number' ? v : null)} />
      <DecimalField id="dtc-add-lon" label={t('dtc.fields.lon')} kind="lon" value={lon} onCommit={(v) => setLon(typeof v === 'number' ? v : null)} />
      <button type="button" className="btn" disabled={disabled || !ready} onClick={() => { if (ready) { onAdd(lat, lon); setLat(null); setLon(null); setRound((r) => r + 1); } }}>
        {t('dtc.points.addTyped')}
      </button>
    </div>
  );
}

/** Editable points of the active list, plus "add by typing coordinates". */
export function PointList({ model, list, approx, serverIssues, actions }: Props) {
  const { t } = useTranslation();
  const points = getPoints(model, list);
  const problems = new Map(serverIssues.filter((i) => i.pointId).map((i) => [i.pointId, i.message]));
  return (
    <div>
      {points.length === 0 ? (
        <p className="muted dtc-empty">{t('dtc.points.empty')}</p>
      ) : (
        <ol className="dtc-points">
          {points.map((p, i) => (
            <PointCard
              key={p.id ?? i} model={model} list={list} point={p} index={i} count={points.length}
              approx={!!(p.id && approx[p.id])} problem={p.id ? problems.get(p.id) : undefined} actions={actions}
            />
          ))}
        </ol>
      )}
      <AddByCoords disabled={!model.terrain} onAdd={actions.addAt} />
    </div>
  );
}
