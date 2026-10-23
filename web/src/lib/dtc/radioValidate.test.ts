import { describe, expect, it } from 'vitest';
import type { DtcAircraft } from '../../api/types.dtc';
import { setChannelFrequency, setInitialHf, setPresetRadio } from './radioEdit';
import { ah64WithRadios, f16WithRadios } from './radioFixtures';
import { radioInputIssues, radioIssues } from './radioValidate';
import { blockingIssues, validateDraft } from './validate';

const info: DtcAircraft = { id: 'F-16C_50', label: 'F-16C', enabled: true, supports: ['radios'], unsupported: [], limits: { waypoints: 25, lines: 4 }, notes: [] };

describe('radioIssues', () => {
  it('has nothing to say about the default radios', () => {
    expect(radioIssues(f16WithRadios())).toEqual([]);
    expect(radioIssues(ah64WithRadios())).toEqual([]);
  });

  it('warns (never blocks) for frequencies outside the documented band', () => {
    const m = setChannelFrequency(setChannelFrequency(f16WithRadios(), 'COMM1', 1, 500), 'COMM2', 4, 90);
    expect(radioIssues(m)).toEqual([{ key: 'radioRange', severity: 'warning', params: { count: 2 } }]);
    expect(blockingIssues(validateDraft(m, info))).toEqual([]);
    expect(validateDraft(m, info).map((i) => i.key)).toContain('radioRange');
  });

  it('blocks a frequency that is not a number greater than 0', () => {
    const zero = setChannelFrequency(f16WithRadios(), 'COMM1', 1, 0);
    expect(radioIssues(zero)[0]).toMatchObject({ key: 'radioBadFrequency', severity: 'error', params: { count: 1 } });
    expect(blockingIssues(validateDraft(zero, info)).map((i) => i.key)).toContain('radioBadFrequency');
    const nan = setPresetRadio(ah64WithRadios(), 2, 'UHF', { frequency_mhz: Number.NaN });
    expect(radioIssues(nan).map((i) => i.key)).toEqual(['radioBadFrequency']);
  });

  it('checks the AH-64 bands per radio, HF initial rx included', () => {
    const m = setInitialHf(setPresetRadio(ah64WithRadios(), 1, 'FM1', { frequency_mhz: 200 }), { rx: { frequency_mhz: 5.65 }, tx: { frequency_mhz: 100 } });
    expect(radioIssues(m)).toEqual([{ key: 'radioRange', severity: 'warning', params: { count: 2 } }]);
  });
});

describe('radioInputIssues', () => {
  it('blocks while some field holds text that is not valid yet', () => {
    expect(radioInputIssues(0)).toEqual([]);
    expect(radioInputIssues(2)).toEqual([{ key: 'radioInvalidInput', severity: 'error', params: { count: 2 } }]);
  });
});
