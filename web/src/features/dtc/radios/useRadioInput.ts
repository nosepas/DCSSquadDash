import { useEffect, useState } from 'react';
import type { ReportInvalid } from './RadioProps';

type Parsed<T> = { ok: true; value: T } | { ok: false; reason: string };

interface Opts<T> {
  id: string;
  value: T | undefined;
  format: (v: T | undefined) => string;
  parse: (text: string) => Parsed<T>;
  onCommit: (v: T) => void;
  report: ReportInvalid;
}

/**
 * Text that only commits valid values (like the coordinate fields): while it is invalid the model keeps the last good value,
 * the error is shown, the download waits, and leaving the field reverts the text.
 */
export function useRadioInput<T>({ id, value, format, parse, onCommit, report }: Opts<T>) {
  const [text, setText] = useState(format(value));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const p = parse(text);
    if (!p.ok || p.value !== value) {
      setText(format(value));
      setError(null);
      report(id, false);
    }
    // Only outside changes (reset, import) matter, not our own typing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  useEffect(() => () => report(id, false), [id, report]);

  const change = (next: string) => {
    setText(next);
    const p = parse(next);
    setError(p.ok ? null : p.reason);
    report(id, !p.ok);
    if (p.ok) onCommit(p.value);
  };
  const blur = () => {
    setText(format(value));
    setError(null);
    report(id, false);
  };
  return { text, error, change, blur };
}
