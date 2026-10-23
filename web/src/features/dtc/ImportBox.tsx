import { useRef, useState, type DragEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { errorKey } from '../../lib/errors';
import type { useDtcImport } from './useDtcImport';

type Importer = ReturnType<typeof useDtcImport>;

/** "Import an existing .dtc": file picker or drag and drop. */
export function ImportBox({ importer, fileName }: { importer: Importer; fileName: string | null }) {
  const { t } = useTranslation();
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  const pick = (file: File | undefined) => {
    if (file) void importer.run(file);
    if (input.current) input.current.value = '';
  };
  const drop = (e: DragEvent) => {
    e.preventDefault();
    setOver(false);
    pick(e.dataTransfer.files[0]);
  };

  return (
    <div className="field">
      <span className="field-label">{t('dtc.steps.import')}</span>
      <div
        className={`dtc-drop${over ? ' dtc-drop-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={drop}
      >
        <button type="button" className="btn" disabled={importer.busy} onClick={() => input.current?.click()}>
          {importer.busy ? t('dtc.import.busy') : t('dtc.import.button')}
        </button>
        <span className="muted small">{fileName ? t('dtc.import.loaded', { name: fileName }) : t('dtc.import.drop')}</span>
        <input ref={input} type="file" accept=".dtc,application/json" hidden onChange={(e) => pick(e.target.files?.[0])} />
      </div>
      {importer.error && (
        <div className="notice notice-warn" role="alert">
          <p>{importer.error.status === 422 ? t('dtc.import.rejected') : t(`errors.${errorKey(importer.error)}`)}</p>
          {importer.reasons.length > 0 && <ul>{importer.reasons.map((r) => <li key={r}>{r}</li>)}</ul>}
        </div>
      )}
    </div>
  );
}
