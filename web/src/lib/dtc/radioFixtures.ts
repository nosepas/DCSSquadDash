import type { DtcModel } from '../../api/types.dtc';
import type { ChannelRadio, DtcRadios, Preset, PresetRadioId } from '../../api/types.radios';
import { PRESET_RADIOS } from '../../api/types.radios';
import { ah64Model, f16Model } from './fixtures';

const channels = (base: number) => Array.from({ length: 20 }, (_, i) => ({ channel: i + 1, frequency_mhz: base + i, extra: { modulation: 1 } }));

export const f16Radios = (): DtcRadios => ({
  radios: [
    { id: 'COMM1', label: 'COMM1 (UHF)', kind: 'channelised', channels: channels(251) },
    { id: 'COMM2', label: 'COMM2 (VHF)', kind: 'channelised', channels: channels(121), extra: { mirror: true } },
  ] satisfies ChannelRadio[],
});

const BASE_MHZ: Record<PresetRadioId, number> = { FM1: 31, FM2: 41, UHF: 251, VHF: 121, HF_RX: 5, HF_TX: 5 };

const preset = (index: number): Preset => ({
  index, call_sign: `PRE ${index}`, unit_id: `PRESET ${index}`, primary_frequency: 1, dl_net: true,
  radios: Object.fromEntries(PRESET_RADIOS.map((r: PresetRadioId) => [r, { frequency_mhz: BASE_MHZ[r] + index, modulation: r === 'UHF' ? 0 : 1, encryption: 0, extra: { k: index } }])),
  extra: { COMMS: { HF_ALE: 1 } },
});

export const ah64Radios = (): DtcRadios => ({
  presets: Array.from({ length: 10 }, (_, i) => preset(i + 1)),
  initial: {
    FM1: { frequency_mhz: 31.5, modulation: 1, encryption: 0, mode: 0, preset: 1 },
    FM2: { frequency_mhz: 31.5, modulation: 1, encryption: 0, mode: 0, preset: 1 },
    UHF: { frequency_mhz: 305, modulation: 0, encryption: 0, mode: 0, preset: 1 },
    VHF: { frequency_mhz: 127.5, modulation: 0, encryption: 0, mode: 0, preset: 1 },
    HF: { mode: 0, preset: 1, rx: { frequency_mhz: 2, modulation: 2, encryption: 0 }, tx: { frequency_mhz: 2, modulation: 2, encryption: 0 } },
  },
  guard_receiver: true,
});

export const f16WithRadios = (): DtcModel => ({ ...f16Model(), radios: f16Radios() });
export const ah64WithRadios = (): DtcModel => ({ ...ah64Model(), radios: ah64Radios() });
