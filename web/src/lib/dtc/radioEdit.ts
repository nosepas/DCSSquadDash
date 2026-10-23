import type { DtcModel } from '../../api/types.dtc';
import type { AhInitial, DtcRadios, InitialRadioId, Preset, PresetRadioId, RadioChannel, RadioInitial, RadioSettings } from '../../api/types.radios';

/**
 * Every helper is immutable: only the edited branch is copied, the rest of the model keeps its identity.
 * Nothing is ever added that was not edited (no normalising), so an unedited file stays byte-identical.
 */
const withRadios = (model: DtcModel, fn: (r: DtcRadios) => DtcRadios): DtcModel => (model.radios ? { ...model, radios: fn(model.radios) } : model);

const mapAt = <T>(arr: T[], match: (x: T) => boolean, fn: (x: T) => T): T[] => arr.map((x) => (match(x) ? fn(x) : x));

/** Sets one channel's frequency; a channel missing from the file is added (kept sorted). `extra` (modulation) is untouched. */
export function setChannelFrequency(model: DtcModel, radioId: string, channel: number, mhz: number): DtcModel {
  return withRadios(model, (r) => ({
    ...r,
    radios: r.radios && mapAt(r.radios, (x) => x.id === radioId, (x) => {
      const list = x.channels ?? [];
      if (!list.some((c) => c.channel === channel)) {
        const added: RadioChannel = { channel, frequency_mhz: mhz };
        return { ...x, channels: [...list, added].sort((a, b) => a.channel - b.channel) };
      }
      return { ...x, channels: mapAt(list, (c) => c.channel === channel, (c) => ({ ...c, frequency_mhz: mhz })) };
    }),
  }));
}

const patchPreset = (model: DtcModel, index: number, fn: (p: Preset) => Preset): DtcModel =>
  withRadios(model, (r) => ({ ...r, presets: r.presets && mapAt(r.presets, (p) => p.index === index, fn) }));

export const setPresetText = (model: DtcModel, index: number, key: 'call_sign' | 'unit_id', value: string): DtcModel =>
  patchPreset(model, index, (p) => ({ ...p, [key]: value }));

export const setPresetRadio = (model: DtcModel, index: number, radio: PresetRadioId, patch: Partial<RadioSettings>): DtcModel =>
  patchPreset(model, index, (p) => ({ ...p, radios: { ...p.radios, [radio]: { ...p.radios?.[radio], ...patch } } }));

const patchInitial = (model: DtcModel, fn: (i: AhInitial) => AhInitial): DtcModel =>
  withRadios(model, (r) => (r.initial ? { ...r, initial: fn(r.initial) } : r));

export const setInitialRadio = (model: DtcModel, radio: InitialRadioId, patch: Partial<RadioInitial>): DtcModel =>
  patchInitial(model, (i) => ({ ...i, [radio]: { ...i[radio], ...patch } }));

/** HF starts on a preset and has separate receive/transmit frequencies. */
export const setInitialHf = (model: DtcModel, patch: { preset?: number; rx?: Partial<RadioSettings>; tx?: Partial<RadioSettings> }): DtcModel =>
  patchInitial(model, (i) => {
    const { rx, tx, ...own } = patch;
    return {
      ...i,
      HF: { ...i.HF, ...own, ...(rx ? { rx: { ...i.HF?.rx, ...rx } } : {}), ...(tx ? { tx: { ...i.HF?.tx, ...tx } } : {}) },
    };
  });

export const setGuardReceiver = (model: DtcModel, on: boolean): DtcModel => withRadios(model, (r) => ({ ...r, guard_receiver: on }));
