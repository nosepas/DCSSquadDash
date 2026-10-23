import { useCallback, useState } from 'react';
import { importDtc } from '../../api/dtc';
import { ApiError } from '../../api/client';
import type { DtcModel } from '../../api/types.dtc';
import { detailTexts } from '../../lib/dtc/errorDetails';

interface Result {
  busy: boolean;
  error: ApiError | null;
  /** Why the file was rejected, one line each (backend wording). */
  reasons: string[];
  warnings: string[];
  run: (file: File) => Promise<void>;
  clear: () => void;
}

/** Uploads a .dtc to /dtc/import and hands the model + template id to `onLoaded`. */
export function useDtcImport(onLoaded: (model: DtcModel, templateId: string, fileName: string) => void): Result {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [reasons, setReasons] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);

  const clear = useCallback(() => {
    setError(null);
    setReasons([]);
    setWarnings([]);
  }, []);

  const run = useCallback(async (file: File) => {
    clear();
    setBusy(true);
    try {
      const res = await importDtc(file);
      setWarnings(res.warnings);
      onLoaded(res.model, res.template_id, file.name);
    } catch (e) {
      const err = e instanceof ApiError ? e : new ApiError(0, 'unknown', 'error');
      setError(err);
      setReasons(detailTexts(err.details));
    } finally {
      setBusy(false);
    }
  }, [clear, onLoaded]);

  return { busy, error, reasons, warnings, run, clear };
}
