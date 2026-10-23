import { describe, expect, it } from 'vitest';
import type { DtcModel } from '../../api/types.dtc';
import { ah64WithRadios, f16WithRadios } from './radioFixtures';
import { setChannelFrequency, setGuardReceiver, setInitialHf, setInitialRadio, setPresetRadio, setPresetText } from './radioEdit';

const untouchedOutsideRadios = (a: DtcModel, b: DtcModel) => {
  expect(b.waypoints).toBe(a.waypoints);
  expect(b.lines).toBe(a.lines);
  expect(b.routes).toBe(a.routes);
  expect(b.aircraft_extra).toBe(a.aircraft_extra);
  expect(b.threat_points).toBe(a.threat_points);
};

describe('F-16 channel edit', () => {
  it('changes one frequency and keeps modulation, mirror and every other channel/radio', () => {
    const m = f16WithRadios();
    const n = setChannelFrequency(m, 'COMM1', 3, 251.5);
    const c1 = n.radios?.radios?.[0];
    expect(c1?.channels?.[2]).toEqual({ channel: 3, frequency_mhz: 251.5, extra: { modulation: 1 } });
    expect(c1?.channels?.[2]?.extra).toBe(m.radios?.radios?.[0]?.channels?.[2]?.extra);
    expect(c1?.channels?.[0]).toBe(m.radios?.radios?.[0]?.channels?.[0]);
    expect(n.radios?.radios?.[1]).toBe(m.radios?.radios?.[1]);
    expect(m.radios?.radios?.[0]?.channels?.[2]?.frequency_mhz).toBe(253);
    untouchedOutsideRadios(m, n);
  });

  it('adds a channel the file did not have, sorted', () => {
    const m = f16WithRadios();
    const cut: DtcModel = { ...m, radios: { radios: [{ id: 'COMM1', channels: [{ channel: 1, frequency_mhz: 100 }, { channel: 5, frequency_mhz: 105 }] }] } };
    const n = setChannelFrequency(cut, 'COMM1', 3, 103);
    expect(n.radios?.radios?.[0]?.channels?.map((c) => c.channel)).toEqual([1, 3, 5]);
  });

  it('is a no-op without radios or for an unknown radio', () => {
    const plain: DtcModel = { ...f16WithRadios(), radios: undefined };
    expect(setChannelFrequency(plain, 'COMM1', 1, 5)).toBe(plain);
    expect(setChannelFrequency(f16WithRadios(), 'COMM9', 1, 5).radios?.radios?.map((r) => r.channels?.[0]?.frequency_mhz)).toEqual([251, 121]);
  });
});

describe('AH-64 edits', () => {
  it('sets call sign and unit id of one preset only', () => {
    const m = ah64WithRadios();
    const n = setPresetText(setPresetText(m, 2, 'call_sign', 'VIPER'), 2, 'unit_id', 'U2');
    const p = n.radios?.presets;
    expect(p?.[1]).toMatchObject({ call_sign: 'VIPER', unit_id: 'U2', primary_frequency: 1, dl_net: true });
    expect(p?.[1]?.extra).toBe(m.radios?.presets?.[1]?.extra);
    expect(p?.[0]).toBe(m.radios?.presets?.[0]);
    expect(p?.[2]).toBe(m.radios?.presets?.[2]);
    expect(n.radios?.initial).toBe(m.radios?.initial);
    untouchedOutsideRadios(m, n);
  });

  it('sets frequency, modulation and encryption of one radio of a preset, keeping its other keys', () => {
    const m = ah64WithRadios();
    let n = setPresetRadio(m, 1, 'UHF', { frequency_mhz: 251 });
    n = setPresetRadio(n, 1, 'VHF', { modulation: 1 });
    n = setPresetRadio(n, 1, 'HF_TX', { encryption: 4 });
    const r = n.radios?.presets?.[0]?.radios;
    expect(r?.UHF).toEqual({ frequency_mhz: 251, modulation: 0, encryption: 0, extra: { k: 1 } });
    expect(r?.VHF?.modulation).toBe(1);
    expect(r?.HF_TX?.encryption).toBe(4);
    expect(r?.FM1).toBe(m.radios?.presets?.[0]?.radios?.FM1);
    expect(n.radios?.presets?.[1]).toBe(m.radios?.presets?.[1]);
    expect(m.radios?.presets?.[0]?.radios?.UHF?.frequency_mhz).toBe(252);
  });

  it('sets initial radios, HF rx/tx/preset and the guard receiver', () => {
    const m = ah64WithRadios();
    let n = setInitialRadio(m, 'UHF', { preset: 4 });
    n = setInitialHf(n, { rx: { frequency_mhz: 5.65 }, preset: 3 });
    n = setGuardReceiver(n, false);
    const i = n.radios?.initial;
    expect(i?.UHF).toEqual({ frequency_mhz: 305, modulation: 0, encryption: 0, mode: 0, preset: 4 });
    expect(i?.HF).toMatchObject({ mode: 0, preset: 3, rx: { frequency_mhz: 5.65, modulation: 2 } });
    expect(i?.HF?.tx).toBe(m.radios?.initial?.HF?.tx);
    expect(i?.FM1).toBe(m.radios?.initial?.FM1);
    expect(n.radios?.guard_receiver).toBe(false);
    expect(n.radios?.presets).toBe(m.radios?.presets);
    untouchedOutsideRadios(m, n);
  });
});
