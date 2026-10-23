import { describedBy, FieldShell } from './FieldShell';

interface Props {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  help?: string;
  error?: string;
  optional?: string;
  mono?: boolean;
  multiline?: boolean;
  placeholder?: string;
  maxLength?: number;
  required?: boolean;
}

export function TextField({ id, label, value, onChange, help, error, optional, mono, multiline, placeholder, maxLength, required }: Props) {
  const common = {
    id,
    value,
    placeholder,
    maxLength,
    required,
    className: mono ? 'mono' : undefined,
    'aria-invalid': error ? true : undefined,
    'aria-describedby': describedBy(id, help, error),
    autoComplete: 'off',
    spellCheck: false,
  };
  return (
    <FieldShell id={id} label={label} help={help} error={error} optional={optional}>
      {multiline ? (
        <textarea rows={3} {...common} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <input type="text" {...common} onChange={(e) => onChange(e.target.value)} />
      )}
    </FieldShell>
  );
}
