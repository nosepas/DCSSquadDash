import type { DtcModel } from '../../../api/types.dtc';
import type { DtcRadios } from '../../../api/types.radios';
import type { RadioActions } from './useRadioActions';

/** Reports whether a field currently holds text that is not valid yet. */
export type ReportInvalid = (id: string, invalid: boolean) => void;

export interface RadioProps {
  model: DtcModel;
  /** Radios as first loaded: reset target and "changed" markers. */
  base: DtcRadios | undefined;
  /** The draft comes from an imported file (reset restores the file's values) instead of the defaults. */
  fromFile: boolean;
  act: RadioActions;
  report: ReportInvalid;
}
