/** File name from a Content-Disposition header (RFC 6266): prefers `filename*`, falls back to `filename`, then `fallback`. */
export function parseContentDisposition(header: string | null | undefined, fallback: string): string {
  if (!header) return fallback;
  const extended = /filename\*\s*=\s*([^;]+)/i.exec(header)?.[1]?.trim();
  const plain = /(?<![*\w])filename\s*=\s*("(?:[^"\\]|\\.)*"|[^;]+)/i.exec(header)?.[1]?.trim();
  const candidate = decodeExtended(extended) ?? unquote(plain);
  return cleanName(candidate) ?? fallback;
}

function decodeExtended(value: string | undefined): string | null {
  if (!value) return null;
  const m = /^([\w-]*)'[^']*'(.*)$/.exec(value);
  try {
    return decodeURIComponent(m ? (m[2] ?? '') : value);
  } catch {
    return null;
  }
}

function unquote(value: string | undefined): string | null {
  if (!value) return null;
  return value.length >= 2 && value.startsWith('"') && value.endsWith('"') ? value.slice(1, -1).replace(/\\(.)/g, '$1') : value;
}

/** Drops any directory part and control characters, so a header can never choose where the file lands. */
function cleanName(name: string | null): string | null {
  if (!name) return null;
  const base = (name.split(/[\\/]/).pop() ?? '')
    .split('')
    .filter((c) => c.charCodeAt(0) >= 32)
    .join('')
    .trim();
  return base && base !== '.' && base !== '..' ? base : null;
}
