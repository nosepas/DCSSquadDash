export interface SegItem {
  id: string;
  label: string;
  /** Marks a tab whose content differs from the original. */
  changed?: boolean;
}

interface Props {
  items: SegItem[];
  value: string;
  onChange: (id: string) => void;
  label: string;
  changedLabel: string;
}

/** Segmented tabs (existing `.segmented` style); the panel is labelled by the selected tab (`rd-tab-<id>`). */
export function SegTabs({ items, value, onChange, label, changedLabel }: Props) {
  return (
    <div className="segmented rd-tabs" role="tablist" aria-label={label}>
      {items.map((i) => (
        <button
          key={i.id} id={`rd-tab-${i.id}`} type="button" role="tab" aria-selected={i.id === value} aria-controls="rd-panel"
          className={i.id === value ? 'active' : ''} onClick={() => onChange(i.id)}
        >
          {i.label}
          {i.changed && <span className="rd-dot" role="img" aria-label={changedLabel} />}
        </button>
      ))}
    </div>
  );
}
