import { useTranslation } from 'react-i18next';
import { PLANE_SVG } from './aircraftMarkers';
import type { MapAircraft, Side } from './useMapAircraft';

/** Legend entries for the aircraft layer: visibility toggle and (admins only) a side selector. */
export function AircraftLegend({ air }: { air: MapAircraft }) {
  const { t } = useTranslation();
  if (!air.authed) return null;
  const count = air.response?.aircraft.length ?? 0;
  return (
    <>
      <li>
        <label className="legend-toggle">
          <input type="checkbox" checked={air.visible} onChange={(e) => air.setVisible(e.target.checked)} />
          <span className="plane-icon plane-legend" aria-hidden="true" dangerouslySetInnerHTML={{ __html: PLANE_SVG }} />
          {t('aircraft.layer')} <span className="muted">({t('aircraft.count', { count })})</span>
        </label>
      </li>
      {air.isAdmin && (
        <li>
          <label className="legend-toggle">
            {t('aircraft.side')}
            <select value={air.side ?? ''} onChange={(e) => air.setSide((e.target.value || undefined) as Side | undefined)}>
              <option value="">{t('aircraft.both')}</option>
              <option value="red">{t('coalition.red')}</option>
              <option value="blue">{t('coalition.blue')}</option>
            </select>
          </label>
        </li>
      )}
    </>
  );
}
