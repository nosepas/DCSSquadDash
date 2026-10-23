import { useTranslation } from 'react-i18next';
import type { ServerSummary } from '../../../api/types';
import type { LayerPrefs } from '../../../lib/dtc/layerPrefs';

interface Toggle {
  key: keyof LayerPrefs;
  label: string;
  disabled: boolean;
  swatches: string[];
}

interface Props {
  prefs: LayerPrefs;
  onToggle: (key: keyof LayerPrefs) => void;
  matches: ServerSummary[];
  selectedId: string | undefined;
  onPickServer: (id: string) => void;
  /** i18n keys of what could not be loaded (shown as a status line). */
  problems: string[];
}

/** Compact "Map layers" control: three toggles that double as legend, the reference server and the orientation-only note. */
export function LayersPanel({ prefs, onToggle, matches, selectedId, onPickServer, problems }: Props) {
  const { t } = useTranslation();
  const noServer = matches.length === 0;
  const toggles: Toggle[] = [
    { key: 'airports', label: t('dtc.layers.airports'), disabled: false, swatches: ['ref-sw ref-sw-civil', 'ref-sw ref-sw-military'] },
    { key: 'front', label: t('dtc.layers.front'), disabled: noServer, swatches: ['ref-sw ref-sw-red', 'ref-sw ref-sw-blue', 'ref-sw-line'] },
    { key: 'farps', label: t('dtc.layers.farps'), disabled: noServer, swatches: ['ref-sw ref-sw-farp'] },
  ];
  return (
    <fieldset className="dtc-layers">
      <legend>{t('dtc.layers.title')}</legend>
      <div className="dtc-layers-toggles">
        {toggles.map((x) => (
          <label key={x.key} className={`dtc-layer-toggle${x.disabled ? ' is-disabled' : ''}`}>
            <input type="checkbox" checked={prefs[x.key] && !x.disabled} disabled={x.disabled} onChange={() => onToggle(x.key)} />
            <span className="dtc-layer-swatches" aria-hidden="true">
              {x.swatches.map((c) => <span key={c} className={c} />)}
            </span>
            {x.label}
          </label>
        ))}
      </div>
      {noServer ? (
        <p className="muted small" role="status">{t('dtc.layers.noServer')}</p>
      ) : (
        <label className="dtc-layers-server">
          <span>{t('dtc.layers.server')}</span>
          <select value={selectedId ?? ''} onChange={(e) => onPickServer(e.target.value)}>
            {matches.map((s) => <option key={s.server_id} value={s.server_id}>{s.name}</option>)}
          </select>
        </label>
      )}
      {problems.map((k) => <p key={k} className="small dtc-layers-problem" role="status">{t(k)}</p>)}
      <p className="muted small">{t('dtc.layers.note')}</p>
    </fieldset>
  );
}
