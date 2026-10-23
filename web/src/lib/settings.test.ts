import { describe, expect, it } from 'vitest';
import type { ServerSettings } from '../api/types.admin';
import { blankToNull, isDirty, mergeSection } from './settings';

const base: ServerSettings = {
  foothold: { enabled: true, saves_dir: 'C:/saves' },
  tacview: { enabled: false, folder: null },
  missions: { folder: null },
  dcsbot: { rest_enabled: true, rest_url: 'http://localhost:9876', rest_prefix: '', server_name: 'Bot1', db_enabled: false },
};

describe('settings helpers', () => {
  it('editing one section keeps the others untouched and does not mutate the input', () => {
    const merged = mergeSection(base, 'tacview', { enabled: true, folder: 'D:/tv' });
    expect(merged.tacview).toEqual({ enabled: true, folder: 'D:/tv' });
    expect(merged.foothold).toBe(base.foothold);
    expect(merged.dcsbot).toBe(base.dcsbot);
    expect(merged.missions).toBe(base.missions);
    expect(base.tacview.enabled).toBe(false);
    expect(Object.keys(merged).sort()).toEqual(['dcsbot', 'foothold', 'missions', 'tacview']);
  });

  it('turns blank text into null', () => {
    expect(blankToNull('  ')).toBeNull();
    expect(blankToNull(null)).toBeNull();
    expect(blankToNull(' C:/x ')).toBe('C:/x');
  });

  it('detects unsaved changes', () => {
    expect(isDirty(base.foothold, { ...base.foothold })).toBe(false);
    expect(isDirty(base.foothold, { ...base.foothold, enabled: false })).toBe(true);
  });
});
