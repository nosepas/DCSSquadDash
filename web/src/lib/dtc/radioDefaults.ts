import type { DtcModel } from '../../api/types.dtc';
import type { Draft } from './draft';

/**
 * What to do when a draft has no radio data although its aircraft supports radios (typically a draft saved before radios existed):
 * - 'auto': fill in the default radios silently (the draft started from the built-in template, so nothing of a file is lost);
 * - 'ask':  the draft comes from an imported file whose radios must not be overwritten by accident: offer an explicit button;
 * - 'none': nothing to do.
 */
export type RadioFill = 'auto' | 'ask' | 'none';

export function radioFillMode(draft: Draft | null, supported: boolean): RadioFill {
  if (!draft || !supported || draft.model.radios) return 'none';
  return draft.templateId === null ? 'auto' : 'ask';
}

/** Adds the radios of a default model to the draft and makes them the baseline; points, lines and everything else stay as they are. */
export function withDefaultRadios(draft: Draft, defaults: DtcModel): Draft {
  if (!defaults.radios) return draft;
  return { ...draft, model: { ...draft.model, radios: defaults.radios }, radiosBase: defaults.radios };
}
