import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { formatCoord, formatElevation, isTimeOfDay, parseCoord, parseElevation } from '../../lib/dtc/coords';

export type FieldKind = 'lat' | 'lon' | 'elev' | 'num' | 'time';

type Parsed = { ok: true; value: number | string | null } | { ok: false; reason: string };

function parse(kind: FieldKind, text: string): Parsed {
  if (kind === 'lat' || kind === 'lon') return parseCoord(text, kind);
  if (kind === 'time') return isTimeOfDay(text.trim()) ? { ok: true, value: text.trim() === '' ? null : text.trim() } : { ok: false, reason: 'time' };
  const r = parseElevation(text);
  return r.ok ? r : { ok: false, reason: 'invalid' };
}

const show = (kind: FieldKind, v: number | string | null | undefined): string => {
  if (v === null || v === undefined) return '';
  if (typeof v === 'string') return v;
  return kind === 'lat' || kind === 'lon' ? formatCoord(v) : formatElevation(v);
};

interface Props {
  id: string;
  label: string;
  kind: FieldKind;
  value: number | string | null | undefined;
  onCommit: (v: number | string | null) => void;
  placeholder?: string;
  /** Small marker under the field, e.g. "approximate". */
  hint?: string;
}

/** Text input that only commits valid values: while the text is invalid the model keeps its last good value and the error is shown. */
export function DecimalField({ id, label, kind, value, onCommit, placeholder, hint }: Props) {
  const { t } = useTranslation();
  const [text, setText] = useState(show(kind, value));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const parsed = parse(kind, text);
    if (!parsed.ok || parsed.value !== (value ?? null)) setText(show(kind, value));
    // Only react to outside changes (drag, elevation lookup), not to our own typing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, kind]);

  const change = (next: string) => {
    setText(next);
    const parsed = parse(kind, next);
    if (!parsed.ok) return setError(parsed.reason);
    setError(null);
    onCommit(parsed.value);
  };

  return (
    <div className={`dtc-num${error ? ' field-invalid' : ''}`}>
      <label htmlFor={id} className="dtc-num-label">{label}</label>
      <input
        id={id} type="text" inputMode={kind === 'time' ? 'numeric' : 'decimal'} value={text} placeholder={placeholder} autoComplete="off" spellCheck={false}
        aria-invalid={error ? true : undefined} aria-describedby={error ? `${id}-err` : undefined}
        onChange={(e) => change(e.target.value)}
        onBlur={() => { setText(show(kind, value)); setError(null); }}
      />
      {error && <small id={`${id}-err`} className="field-error" role="alert">{t(`dtc.fields.errors.${error}`)}</small>}
      {!error && hint && <small className="dtc-approx">{hint}</small>}
    </div>
  );
}
