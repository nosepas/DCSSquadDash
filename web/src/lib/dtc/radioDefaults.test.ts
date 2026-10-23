import { describe, expect, it } from 'vitest';
import type { DtcModel } from '../../api/types.dtc';
import { newDraft } from './draft';
import { radioFillMode, withDefaultRadios } from './radioDefaults';

const radios = { radios: [{ id: 'COMM1', channels: [{ channel: 1, frequency_mhz: 305 }] }] } as unknown as DtcModel['radios'];
const model = (withRadios = false): DtcModel =>
  ({
    model_version: 1, terrain: 'Syria', aircraft: 'F-16C_50', name: '', waypoints: [{ lat: 1, lon: 2, elevation_m: 3, name: 'A' }],
    routes: [], lines: [], aircraft_extra: { keep: 1 }, ...(withRadios ? { radios } : {}),
  }) as DtcModel;

describe('radioFillMode', () => {
  it('repairs old drafts silently, asks before touching an imported file, and ignores the rest', () => {
    expect(radioFillMode(newDraft(model()), true)).toBe('auto');
    expect(radioFillMode(newDraft(model(), 'tpl', 'my.dtc'), true)).toBe('ask');
    expect(radioFillMode(newDraft(model(true)), true)).toBe('none');
    expect(radioFillMode(newDraft(model()), false)).toBe('none');
    expect(radioFillMode(null, true)).toBe('none');
  });
});

describe('withDefaultRadios', () => {
  it('only adds radios and baseline: the rest of the draft keeps its identity', () => {
    const d = newDraft(model());
    const out = withDefaultRadios(d, model(true));
    expect(out.model.radios).toBe(radios);
    expect(out.radiosBase).toBe(radios);
    expect(out.model.waypoints).toBe(d.model.waypoints);
    expect(out.model.aircraft_extra).toBe(d.model.aircraft_extra);
    expect(out.templateId).toBe(d.templateId);
  });

  it('leaves the draft alone when the server model has no radios', () => {
    const d = newDraft(model());
    expect(withDefaultRadios(d, model())).toBe(d);
  });
});
