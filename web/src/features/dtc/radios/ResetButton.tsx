import { useTranslation } from 'react-i18next';

interface Props {
  disabled: boolean;
  fromFile: boolean;
  onReset: () => void;
}

/** "Reset to defaults" (or "restore the values of your file" for an imported draft); disabled while nothing changed. */
export function ResetButton({ disabled, fromFile, onReset }: Props) {
  const { t } = useTranslation();
  return (
    <button type="button" className="btn btn-ghost" disabled={disabled} onClick={onReset}>
      {t(fromFile ? 'dtc.radios.resetFile' : 'dtc.radios.reset')}
    </button>
  );
}
