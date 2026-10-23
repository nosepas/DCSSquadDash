import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

interface DirtyValue {
  count: number;
  report: (id: string, dirty: boolean) => void;
}

const DirtyContext = createContext<DirtyValue | null>(null);

/** Collects which form sections have unsaved edits so the page can protect them. */
export function DirtyProvider({ children }: { children: (dirtyCount: number) => ReactNode }) {
  const [dirty, setDirty] = useState<ReadonlySet<string>>(new Set());
  const report = useCallback((id: string, isDirty: boolean) => {
    setDirty((prev) => {
      if (prev.has(id) === isDirty) return prev;
      const next = new Set(prev);
      if (isDirty) next.add(id);
      else next.delete(id);
      return next;
    });
  }, []);
  const value = useMemo(() => ({ count: dirty.size, report }), [dirty.size, report]);
  return <DirtyContext.Provider value={value}>{children(dirty.size)}</DirtyContext.Provider>;
}

/** Registers a section as dirty while it has unsaved changes (and clears it on unmount). */
export function useDirtyReport(id: string, dirty: boolean): void {
  const ctx = useContext(DirtyContext);
  const report = ctx?.report;
  useEffect(() => {
    report?.(id, dirty);
    return () => report?.(id, false);
  }, [report, id, dirty]);
}
