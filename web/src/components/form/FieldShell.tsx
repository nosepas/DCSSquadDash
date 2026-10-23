import type { ReactNode } from 'react';

interface Props {
  id: string;
  label: string;
  help?: string;
  error?: string;
  optional?: string;
  children: ReactNode;
}

/** Ids of the help/error paragraphs, to be used as `aria-describedby` on the control. */
export const describedBy = (id: string, help?: string, error?: string): string | undefined => {
  const ids = [help ? `${id}-help` : '', error ? `${id}-err` : ''].filter(Boolean).join(' ');
  return ids || undefined;
};

/** Label + control + plain-language help line + inline validation error. */
export function FieldShell({ id, label, help, error, optional, children }: Props) {
  return (
    <div className={`field ${error ? 'field-invalid' : ''}`}>
      <label htmlFor={id} className="field-label">
        {label}
        {optional && <span className="field-optional"> ({optional})</span>}
      </label>
      {children}
      {help && <p id={`${id}-help`} className="field-help">{help}</p>}
      {error && <p id={`${id}-err`} className="field-error" role="alert">{error}</p>}
    </div>
  );
}
