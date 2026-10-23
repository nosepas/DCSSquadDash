import type { DtcModel } from '../../api/types.dtc';
import type { DtcRadios } from '../../api/types.radios';

/*
 * The baseline is the radio block as first loaded (default-model or imported file).
 * "Reset" restores it and the change markers compare against it.
 */
export const freqOf = (radios: DtcRadios | undefined, radioId: string, channel: number): number | undefined =>
  radios?.radios?.find((r) => r.id === radioId)?.channels?.find((c) => c.channel === channel)?.frequency_mhz;

export const channelChanged = (model: DtcModel, base: DtcRadios | undefined, radioId: string, channel: number): boolean =>
  base !== undefined && freqOf(model.radios, radioId, channel) !== freqOf(base, radioId, channel);

const same = (a: unknown, b: unknown): boolean => a === b || JSON.stringify(a) === JSON.stringify(b);

/** Any radio value differs from the baseline (asks for confirmation before the draft is replaced). */
export const radiosEdited = (model: DtcModel, base: DtcRadios | undefined): boolean => base !== undefined && !same(model.radios, base);

export const radioChanged = (model: DtcModel, base: DtcRadios | undefined, radioId: string): boolean =>
  base !== undefined && !same(model.radios?.radios?.find((r) => r.id === radioId), base.radios?.find((r) => r.id === radioId));

export const presetChanged = (model: DtcModel, base: DtcRadios | undefined, index: number): boolean =>
  base !== undefined && !same(model.radios?.presets?.find((p) => p.index === index), base.presets?.find((p) => p.index === index));

export const initialChanged = (model: DtcModel, base: DtcRadios | undefined): boolean =>
  base !== undefined && (!same(model.radios?.initial, base.initial) || !same(model.radios?.guard_receiver, base.guard_receiver));

/** Puts the baseline version of one F-16 radio back (everything else untouched). */
export function resetRadio(model: DtcModel, base: DtcRadios | undefined, radioId: string): DtcModel {
  const orig = base?.radios?.find((r) => r.id === radioId);
  if (!orig || !model.radios?.radios) return model;
  return { ...model, radios: { ...model.radios, radios: model.radios.radios.map((r) => (r.id === radioId ? orig : r)) } };
}

export function resetPreset(model: DtcModel, base: DtcRadios | undefined, index: number): DtcModel {
  const orig = base?.presets?.find((p) => p.index === index);
  if (!orig || !model.radios?.presets) return model;
  return { ...model, radios: { ...model.radios, presets: model.radios.presets.map((p) => (p.index === index ? orig : p)) } };
}

/** Initial settings and the guard receiver go back together. */
export function resetInitial(model: DtcModel, base: DtcRadios | undefined): DtcModel {
  if (!base?.initial || !model.radios) return model;
  const guard = base.guard_receiver === undefined ? {} : { guard_receiver: base.guard_receiver };
  return { ...model, radios: { ...model.radios, initial: base.initial, ...guard } };
}
