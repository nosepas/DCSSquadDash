import { useCallback, useRef, useState } from 'react';
import { ApiError } from '../../api/client';
import { tacviewDownloadUrl } from '../../api/tacview';
import type { TacviewHit } from '../../api/types.tacview';
import { fetchFile, saveBlob } from '../../lib/download';
import { downloadErrorKey } from '../../lib/tacview';

export interface DownloadState {
  fileId: number | null;
  phase: 'idle' | 'asking' | 'downloading';
  /** 0..100, or null when the size is unknown. */
  percent: number | null;
  errorKey: string | null;
  errorFile: string | null;
}

const IDLE: DownloadState = { fileId: null, phase: 'idle', percent: null, errorKey: null, errorFile: null };

/**
 * One Tacview download at a time. While the agent has not answered the phase is "asking" (up to ~30 s);
 * errors are mapped to message keys before any browser download starts.
 */
export function useTacviewDownload() {
  const [state, setState] = useState<DownloadState>(IDLE);
  const ctrl = useRef<AbortController | null>(null);

  const cancel = useCallback(() => {
    ctrl.current?.abort();
    setState(IDLE);
  }, []);

  const start = useCallback(async (hit: TacviewHit) => {
    ctrl.current?.abort();
    const c = new AbortController();
    ctrl.current = c;
    setState({ ...IDLE, fileId: hit.file_id, phase: 'asking' });
    const fallback = hit.file.split(/[\\/]/).pop() ?? 'recording.acmi';
    try {
      const file = await fetchFile(tacviewDownloadUrl(hit.file_id), fallback, {
        signal: c.signal,
        onStart: (total) => setState((s) => ({ ...s, phase: 'downloading', percent: total ? 0 : null })),
        onProgress: (got, total) => total && setState((s) => ({ ...s, percent: Math.floor((got / total) * 100) })),
      });
      saveBlob(file);
      setState(IDLE);
    } catch (e) {
      if (c.signal.aborted) return;
      const err = e instanceof ApiError ? e : new ApiError(0, 'unknown', 'error');
      setState({ ...IDLE, errorKey: downloadErrorKey(err.status, err.code), errorFile: hit.file });
    }
  }, []);

  return { state, start, cancel };
}
