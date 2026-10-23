import { useEffect, useState, type FormEvent } from 'react';
import { useAction } from '../../../hooks/useAction';
import { fieldErrors } from '../../../lib/fieldErrors';
import { isDirty } from '../../../lib/settings';
import { useDirtyReport } from './dirty';

/**
 * Draft state for one settings section: tracks unsaved edits, runs the save and exposes inline API errors.
 * The draft is reset only when the saved value itself changes, so background status refreshes never wipe edits.
 */
export function useSectionForm<T>(id: string, saved: T, save: (draft: T) => Promise<unknown>) {
  const [draft, setDraft] = useState<T>(saved);
  const [ok, setOk] = useState(false);
  const action = useAction();
  const savedKey = JSON.stringify(saved);

  useEffect(() => {
    setDraft(JSON.parse(savedKey) as T);
  }, [savedKey]);

  const dirty = isDirty(saved, draft);
  useDirtyReport(id, dirty);

  const submit = async (e?: FormEvent) => {
    e?.preventDefault();
    setOk(false);
    if (await action.run(() => save(draft))) setOk(true);
  };

  const edit = (patch: Partial<T>) => {
    setOk(false);
    setDraft((d) => ({ ...d, ...patch }));
  };

  return { draft, edit, dirty, busy: action.busy, error: action.error, errors: fieldErrors(action.error), ok: ok && !dirty, submit };
}

export type SectionForm = Pick<ReturnType<typeof useSectionForm>, 'dirty' | 'busy' | 'error' | 'ok' | 'submit'>;
