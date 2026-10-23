import { useTranslation } from 'react-i18next';
import type { DtcModel } from '../../api/types.dtc';
import { listInfos } from '../../lib/dtc/listInfo';
import { sameRef, type ListRef } from '../../lib/dtc/lists';

interface Props {
  model: DtcModel;
  active: ListRef;
  onSelect: (ref: ListRef) => void;
}

/** Chips for every list (steerpoints, route slots, lines, missions). The colour dot doubles as the map legend. */
export function ListSelector({ model, active, onSelect }: Props) {
  const { t } = useTranslation();
  return (
    <div role="group" aria-label={t('dtc.lists.aria')} className="dtc-lists">
      {listInfos(model).map((l) => {
        const on = sameRef(l.ref, active);
        return (
          <button key={JSON.stringify(l.ref)} type="button" className={`chip${on ? ' chip-active' : ''}`} aria-pressed={on} onClick={() => onSelect(l.ref)}>
            <span className="dtc-swatch" style={{ background: l.color }} aria-hidden="true" />
            {t(`dtc.lists.${l.labelKey}`, l.params)}
            <small>{l.count}</small>
          </button>
        );
      })}
    </div>
  );
}
