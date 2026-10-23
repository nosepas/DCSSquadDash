import { useTranslation } from 'react-i18next';
import type { DtcModel } from '../../api/types.dtc';
import { lineRoute, routeAsLine } from '../../lib/dtc/f14';
import type { ListRef } from '../../lib/dtc/lists';
import type { useDtcActions } from './useDtcActions';

type Actions = ReturnType<typeof useDtcActions>;

interface Props {
  model: DtcModel;
  active: ListRef;
  actions: Actions;
}

/** F-14 only: rename the route slot, draw it as a line, close/delete a line, add a new line. */
export function ListSettings({ model, active, actions }: Props) {
  const { t } = useTranslation();
  if (model.aircraft !== 'F-14BU') return null;
  return (
    <div className="dtc-settings">
      {active.type === 'route' && (
        <>
          <label className="field">
            <span>{t('dtc.f14.routeName')}</span>
            <input type="text" value={model.routes[active.index]?.name ?? ''} onChange={(e) => actions.routeName(active.index, e.target.value)} />
          </label>
          <label className="check">
            <input type="checkbox" checked={routeAsLine(model, active.index)} onChange={(e) => actions.routeAsLine(active.index, e.target.checked)} />
            {t('dtc.f14.asLine')}
          </label>
          <p className="field-help">{t('dtc.f14.asLineHelp')}</p>
        </>
      )}
      {active.type === 'line' && (
        <>
          <p className="muted small">{t('dtc.f14.lineOf', { route: lineRoute(model, active.index) + 1 })}</p>
          <label className="check">
            <input type="checkbox" checked={model.lines[active.index]?.closed === true} onChange={(e) => actions.closed(active.index, e.target.checked)} />
            {t('dtc.f14.closed')}
          </label>
          <button type="button" className="btn btn-danger" onClick={() => actions.removeLine(active.index)}>{t('dtc.f14.deleteLine')}</button>
        </>
      )}
      <button type="button" className="btn" onClick={actions.addLine}>{t('dtc.f14.addLine')}</button>
    </div>
  );
}
