import { beforeEach, describe, expect, it } from 'vitest';
import { DRAFT_KEY, loadDraft, newDraft, parseDraft, saveDraft, type Draft } from './draft';
import { f14Model } from './fixtures';
import { f16WithRadios } from './radioFixtures';

const draft: Draft = { model: f14Model(), templateId: 'tpl', approx: { r1: true }, active: { type: 'route', index: 1 }, fileName: 'a.dtc' };

describe('draft storage', () => {
  beforeEach(() => window.localStorage.clear());

  it('round-trips through localStorage', () => {
    saveDraft(draft);
    expect(loadDraft()).toEqual(draft);
    saveDraft(null);
    expect(window.localStorage.getItem(DRAFT_KEY)).toBeNull();
    expect(loadDraft()).toBeNull();
  });

  it('discards anything that is not a usable draft', () => {
    expect(parseDraft(null)).toBeNull();
    expect(parseDraft('not json')).toBeNull();
    expect(parseDraft('{"model":{"aircraft":"F-16C_50"},"active":{}}')).toBeNull();
    expect(parseDraft('[]')).toBeNull();
  });

  it('fills optional fields with safe defaults', () => {
    const minimal = JSON.stringify({ model: { ...draft.model }, active: { type: 'waypoints' } });
    expect(parseDraft(minimal)).toMatchObject({ templateId: null, approx: {}, fileName: null });
  });

  it('keeps the radio baseline in the saved draft', () => {
    const d = newDraft(f16WithRadios(), 'tpl', 'a.dtc');
    expect(d.radiosBase).toBe(d.model.radios);
    saveDraft(d);
    expect(loadDraft()?.radiosBase).toEqual(d.model.radios);
  });

  describe('stale or corrupt saved drafts never crash the page', () => {
    const wrap = (active: unknown, model = draft.model) => JSON.stringify({ model, active });
    const routeTwo = { type: 'route', index: 1 };

    it('keeps a list reference that still exists', () => {
      expect(parseDraft(wrap(routeTwo))?.active).toEqual(routeTwo);
      const withLine = { ...draft.model, lines: [{ name: 'L', closed: false, points: [] }] };
      expect(parseDraft(wrap({ type: 'line', index: 0 }, withLine))?.active).toEqual({ type: 'line', index: 0 });
    });

    it.each([
      ['unknown shape (old field name)', { kind: 'waypoints' }],
      ['index out of range', { type: 'route', index: 99 }],
      ['negative or fractional index', { type: 'line', index: -1 }],
      ['index of the wrong type', { type: 'route', index: '1' }],
      ['a list type this aircraft does not have', { type: 'ah64', mission: 1, kind: 'TGT' }],
      ['not an object', 'waypoints'],
      ['missing', undefined],
    ])('falls back to the first list: %s', (_name, active) => {
      const parsed = parseDraft(wrap(active));
      expect(parsed?.active).toEqual({ type: 'route', index: 0 });
    });

    it('discards a draft whose lists are malformed', () => {
      expect(parseDraft(wrap({ type: 'waypoints' }, { ...draft.model, routes: [{ name: 'x' }] } as never))).toBeNull();
      expect(parseDraft(wrap({ type: 'waypoints' }, { ...draft.model, lines: [null] } as never))).toBeNull();
      expect(parseDraft(wrap({ type: 'waypoints' }, { ...draft.model, waypoints: 'oops' } as never))).toBeNull();
    });
  });

  it('starts a draft without baseline for an aircraft without radios and loads old drafts', () => {
    expect(newDraft(f14Model()).radiosBase).toBeUndefined();
    const old = JSON.stringify({ model: { ...draft.model }, active: { type: 'waypoints' } });
    expect(parseDraft(old)?.radiosBase).toBeUndefined();
  });
});
