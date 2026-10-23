import { describe, expect, it } from 'vitest';
import { channelChanged, initialChanged, presetChanged, radioChanged, radiosEdited, resetInitial, resetPreset, resetRadio } from './radioBaseline';
import { setChannelFrequency, setGuardReceiver, setInitialRadio, setPresetText } from './radioEdit';
import { ah64WithRadios, f16WithRadios } from './radioFixtures';

describe('F-16 baseline', () => {
  const m = f16WithRadios();
  const base = m.radios;
  const edited = setChannelFrequency(m, 'COMM2', 2, 130);

  it('marks only what differs from the baseline', () => {
    expect(radiosEdited(m, base)).toBe(false);
    expect(radiosEdited(edited, base)).toBe(true);
    expect(channelChanged(edited, base, 'COMM2', 2)).toBe(true);
    expect(channelChanged(edited, base, 'COMM2', 3)).toBe(false);
    expect(radioChanged(edited, base, 'COMM2')).toBe(true);
    expect(radioChanged(edited, base, 'COMM1')).toBe(false);
  });

  it('never marks anything without a baseline (old drafts)', () => {
    expect(radiosEdited(edited, undefined)).toBe(false);
    expect(channelChanged(edited, undefined, 'COMM2', 2)).toBe(false);
  });

  it('resets one radio to the baseline and leaves the other as edited', () => {
    const both = setChannelFrequency(edited, 'COMM1', 1, 300);
    const back = resetRadio(both, base, 'COMM2');
    expect(back.radios?.radios?.[1]).toBe(base?.radios?.[1]);
    expect(back.radios?.radios?.[0]?.channels?.[0]?.frequency_mhz).toBe(300);
    expect(back.waypoints).toBe(both.waypoints);
    expect(resetRadio(both, base, 'NOPE')).toBe(both);
    expect(resetRadio(both, undefined, 'COMM2')).toBe(both);
  });
});

describe('AH-64 baseline', () => {
  const m = ah64WithRadios();
  const base = m.radios;

  it('detects and resets a preset', () => {
    const e = setPresetText(m, 3, 'call_sign', 'X');
    expect(presetChanged(e, base, 3)).toBe(true);
    expect(presetChanged(e, base, 4)).toBe(false);
    const back = resetPreset(e, base, 3);
    expect(back.radios?.presets?.[2]).toBe(base?.presets?.[2]);
    expect(presetChanged(back, base, 3)).toBe(false);
  });

  it('resets initial settings and guard receiver together', () => {
    const e = setGuardReceiver(setInitialRadio(m, 'FM1', { preset: 9 }), false);
    expect(initialChanged(e, base)).toBe(true);
    const back = resetInitial(e, base);
    expect(back.radios?.initial).toBe(base?.initial);
    expect(back.radios?.guard_receiver).toBe(true);
    expect(initialChanged(back, base)).toBe(false);
    expect(back.radios?.presets).toBe(e.radios?.presets);
  });
});
