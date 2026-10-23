import { useCallback, useEffect, useState } from 'react';
import { ApiError } from '../../api/client';
import { generateDtc } from '../../api/dtc';
import type { Draft } from '../../lib/dtc/draft';
import { saveBlob } from '../../lib/download';
import { mapDetails, type ServerIssue } from '../../lib/dtc/errorDetails';

export interface DownloadResult {
  busy: boolean;
  issues: ServerIssue[];
  /** Server wording for generation warnings (e.g. elevation written as 0). Shown after a successful download. */
  warnings: string[];
  done: boolean;
  /** The imported file is no longer cached on the server (it expires after an hour). */
  templateExpired: boolean;
  /** Any other failure (network, server): shown with a generic message. */
  failure: ApiError | null;
  run: (withTemplate?: boolean) => Promise<void>;
}

/** POSTs the model to /dtc/generate and hands the file to the browser; 422 details are mapped to points. */
export function useDtcDownload(draft: Draft | null, onTemplateDropped: () => void): DownloadResult {
  const [busy, setBusy] = useState(false);
  const [issues, setIssues] = useState<ServerIssue[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  const [templateExpired, setExpired] = useState(false);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const model = draft?.model;

  // Any edit makes the previous answer stale.
  useEffect(() => {
    setIssues([]);
    setDone(false);
    setFailure(null);
  }, [model]);

  const run = useCallback(async (withTemplate = true) => {
    if (!draft) return;
    setBusy(true);
    setIssues([]);
    setWarnings([]);
    setDone(false);
    setFailure(null);
    setExpired(false);
    if (!withTemplate) onTemplateDropped();
    const fallback = `${draft.model.aircraft}_${draft.model.name || 'FOX3'}.dtc`;
    try {
      const file = await generateDtc(draft.model, withTemplate ? draft.templateId : null, fallback);
      saveBlob(file);
      setWarnings(file.warnings);
      setDone(true);
    } catch (e) {
      const err = e instanceof ApiError ? e : new ApiError(0, 'unknown', 'error');
      if (err.status === 422) setIssues(mapDetails(err.details, draft.model));
      else if (err.status === 404 && withTemplate && draft.templateId) setExpired(true);
      else setFailure(err);
    } finally {
      setBusy(false);
    }
  }, [draft, onTemplateDropped]);

  return { busy, issues, warnings, done, templateExpired, failure, run };
}
