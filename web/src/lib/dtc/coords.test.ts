import { describe, expect, it } from 'vitest';
import { formatCoord, formatElevation, isTimeOfDay, parseCoord, parseElevation } from './coords';

describe('parseCoord', () => {
  it('accepts decimal degrees with dot or comma', () => {
    expect(parseCoord('41.5', 'lat')).toEqual({ ok: true, value: 41.5 });
    expect(parseCoord(' -2,25 ', 'lon')).toEqual({ ok: true, value: -2.25 });
    expect(parseCoord('+10', 'lat')).toEqual({ ok: true, value: 10 });
  });

  it('rejects empty, text and out-of-range values', () => {
    expect(parseCoord('', 'lat')).toEqual({ ok: false, reason: 'required' });
    expect(parseCoord('41°30', 'lat')).toEqual({ ok: false, reason: 'invalid' });
    expect(parseCoord('1e3', 'lon')).toEqual({ ok: false, reason: 'invalid' });
    expect(parseCoord('91', 'lat')).toEqual({ ok: false, reason: 'range' });
    expect(parseCoord('-181', 'lon')).toEqual({ ok: false, reason: 'range' });
    expect(parseCoord('180', 'lon')).toEqual({ ok: true, value: 180 });
  });
});

describe('elevation and formatting', () => {
  it('treats empty as unknown and rejects garbage', () => {
    expect(parseElevation('')).toEqual({ ok: true, value: null });
    expect(parseElevation('12,5')).toEqual({ ok: true, value: 12.5 });
    expect(parseElevation('-3')).toEqual({ ok: true, value: -3 });
    expect(parseElevation('abc')).toEqual({ ok: false });
  });

  it('formats without noise', () => {
    expect(formatCoord(41.12345678)).toBe('41.123457');
    expect(formatCoord(3)).toBe('3');
    expect(formatElevation(null)).toBe('');
    expect(formatElevation(28.956)).toBe('29');
    expect(formatElevation(12.34)).toBe('12.3');
  });

  it('validates times of day', () => {
    expect(['', '10:00:00', '23:59:59'].every(isTimeOfDay)).toBe(true);
    expect(['24:00:00', '1:00', '10:61:00', 'x'].some(isTimeOfDay)).toBe(false);
  });
});
