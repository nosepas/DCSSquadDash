/** Radio part of the neutral DTC model (contracts/schemas/dtc_mission.json, `radios`). `extra` objects travel untouched. */
export type Extra = Record<string, unknown>;

export interface RadioChannel {
  channel: number;
  frequency_mhz: number;
  extra?: Extra;
}

/** F-16C_50 channelised radio: COMM1 = UHF, COMM2 = VHF. */
export interface ChannelRadio {
  id: string;
  label?: string;
  kind?: string;
  channels?: RadioChannel[];
  extra?: Extra;
}

export interface RadioSettings {
  frequency_mhz?: number;
  modulation?: number;
  encryption?: number;
  extra?: Extra;
}

export interface RadioInitial extends RadioSettings {
  mode?: number;
  preset?: number;
}

export interface InitialHf {
  mode?: number;
  preset?: number;
  rx?: RadioSettings;
  tx?: RadioSettings;
  extra?: Extra;
}

export const PRESET_RADIOS = ['FM1', 'FM2', 'UHF', 'VHF', 'HF_RX', 'HF_TX'] as const;
export type PresetRadioId = (typeof PRESET_RADIOS)[number];

export interface Preset {
  index: number;
  call_sign?: string;
  unit_id?: string;
  primary_frequency?: number;
  dl_net?: boolean;
  radios?: Partial<Record<PresetRadioId, RadioSettings>>;
  extra?: Extra;
}

export const INITIAL_RADIOS = ['FM1', 'FM2', 'UHF', 'VHF'] as const;
export type InitialRadioId = (typeof INITIAL_RADIOS)[number];

export interface AhInitial {
  FM1?: RadioInitial;
  FM2?: RadioInitial;
  UHF?: RadioInitial;
  VHF?: RadioInitial;
  HF?: InitialHf;
}

export interface DtcRadios {
  radios?: ChannelRadio[];
  presets?: Preset[];
  initial?: AhInitial;
  guard_receiver?: boolean;
}
