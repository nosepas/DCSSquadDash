import type { DetectedFolder } from '../../../api/types.admin';
import { TextField } from '../../../components/form/TextField';
import { DetectedChips } from './DetectedChips';

interface Props {
  id: string;
  label: string;
  help: string;
  value: string | null;
  onChange: (value: string | null) => void;
  detected: DetectedFolder[] | undefined;
  error?: string;
}

/** Folder input with the agent's detected folders as one-click suggestions. */
export function FolderField({ id, label, help, value, onChange, detected, error }: Props) {
  return (
    <>
      <TextField id={id} label={label} help={help} error={error} mono value={value ?? ''} onChange={(v) => onChange(v === '' ? null : v)} />
      <DetectedChips items={detected} current={value ?? ''} onPick={onChange} />
    </>
  );
}
