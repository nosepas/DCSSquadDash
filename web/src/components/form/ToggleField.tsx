interface Props {
  id: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  help?: string;
}

export function ToggleField({ id, label, checked, onChange, help }: Props) {
  return (
    <div className="field">
      <label className="check" htmlFor={id}>
        <input id={id} type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} aria-describedby={help ? `${id}-help` : undefined} />
        {label}
      </label>
      {help && <p id={`${id}-help`} className="field-help field-help-indented">{help}</p>}
    </div>
  );
}
