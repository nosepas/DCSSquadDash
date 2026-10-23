import { useCallback, useEffect, useRef, useState } from 'react';
import type { DtcModel } from '../../api/types.dtc';
import { loadDraft, newDraft, saveDraft, type Draft } from '../../lib/dtc/draft';

/** The editor's single source of truth, mirrored to localStorage (silently skipped when storage is unavailable). */
export function useDtcDraft() {
  const [draft, setDraft] = useState<Draft | null>(loadDraft);
  const ref = useRef(draft);
  ref.current = draft;
  // Bumped when the whole content is replaced (import, draft restore) so the map re-frames the points.
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const id = window.setTimeout(() => saveDraft(draft), 300);
    return () => window.clearTimeout(id);
  }, [draft]);

  const update = useCallback((fn: (d: Draft) => Draft) => setDraft((d) => (d ? fn(d) : d)), []);
  const editModel = useCallback((fn: (m: DtcModel) => DtcModel) => update((d) => ({ ...d, model: fn(d.model) })), [update]);

  /** Replaces the whole draft with a model from the server (new aircraft: default radios; import: the file's). */
  const begin = useCallback((model: DtcModel) => setDraft(newDraft(model)), []);

  const load = useCallback((model: DtcModel, templateId: string, fileName: string) => {
    setDraft(newDraft(model, templateId, fileName));
    setRevision((r) => r + 1);
  }, []);

  const clear = useCallback(() => setDraft(null), []);
  const dropTemplate = useCallback(() => update((d) => ({ ...d, templateId: null, fileName: null })), [update]);
  return { draft, getModel: () => ref.current?.model ?? null, update, editModel, begin, load, clear, dropTemplate, revision };
}
