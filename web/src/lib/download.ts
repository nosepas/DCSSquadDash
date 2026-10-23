import { ApiError, toApiError } from '../api/client';
import { filenameFromDisposition } from './tacview';

export interface DownloadOptions {
  signal?: AbortSignal;
  /** Called once the server has started sending (the response headers arrived). */
  onStart?: (totalBytes: number | null) => void;
  onProgress?: (receivedBytes: number, totalBytes: number | null) => void;
}

export interface Downloaded {
  blob: Blob;
  filename: string;
}

const networkError = () => new ApiError(0, 'network', 'network error');

/**
 * Fetches a file with the session cookie and returns it as a Blob, so failures (504/404/429...) can be
 * shown as friendly messages BEFORE the browser starts a download. Rejects with ApiError.
 */
export async function fetchFile(url: string, fallbackName: string, opts: DownloadOptions = {}): Promise<Downloaded> {
  let res: Response;
  try {
    res = await fetch(url, { credentials: 'same-origin', signal: opts.signal });
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e;
    throw networkError();
  }
  if (!res.ok) throw await toApiError(res);

  const length = Number(res.headers.get('Content-Length'));
  const total = Number.isFinite(length) && length > 0 ? length : null;
  opts.onStart?.(total);
  const chunks: Uint8Array[] = [];
  let received = 0;
  try {
    const reader = res.body?.getReader();
    if (!reader) throw networkError();
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      received += value.length;
      opts.onProgress?.(received, total);
    }
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e;
    throw e instanceof ApiError ? e : networkError();
  }
  const filename = filenameFromDisposition(res.headers.get('Content-Disposition'), fallbackName);
  return { blob: new Blob(chunks as BlobPart[], { type: 'application/octet-stream' }), filename };
}

/** Hands a Blob to the browser as a regular file download. */
export function saveBlob({ blob, filename }: Downloaded): void {
  const href = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = href;
  a.download = filename;
  document.body.append(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(href), 10_000);
}
