import { describe, expect, it } from 'vitest';
import { formatFrequency, parseFrequency, parseWhole } from './radioFreq';
import { BAND_RANGES, bandOf, isOutOfRange, isUnconfirmedFraction } from './radioRanges';

describe('parseFrequency', () => {
  it('accepts dot and comma decimals and whole numbers', () => {
    expect(parseFrequency('251')).toEqual({ ok: true, value: 251 });
    expect(parseFrequency('127.5')).toEqual({ ok: true, value: 127.5 });
    expect(parseFrequency(' 127,5 ')).toEqual({ ok: true, value: 127.5 });
    expect(parseFrequency('.5')).toEqual({ ok: true, value: 0.5 });
  });

  it('rounds to 3 decimals', () => {
    expect(parseFrequency('251.07549')).toEqual({ ok: true, value: 251.075 });
    expect(parseFrequency('251,0006')).toEqual({ ok: true, value: 251.001 });
  });

  it('rejects empty, non numbers and values that are not greater than 0', () => {
    expect(parseFrequency('')).toEqual({ ok: false, reason: 'required' });
    expect(parseFrequency('abc')).toEqual({ ok: false, reason: 'invalid' });
    expect(parseFrequency('1e3')).toEqual({ ok: false, reason: 'invalid' });
    expect(parseFrequency('0')).toEqual({ ok: false, reason: 'positive' });
    expect(parseFrequency('-5')).toEqual({ ok: false, reason: 'positive' });
    expect(parseFrequency('0.0001')).toEqual({ ok: false, reason: 'positive' });
  });
});

describe('formatFrequency', () => {
  it('has no trailing zeros and at most 3 decimals', () => {
    expect(formatFrequency(251)).toBe('251');
    expect(formatFrequency(127.5)).toBe('127.5');
    expect(formatFrequency(251.0754)).toBe('251.075');
    expect(formatFrequency(undefined)).toBe('');
  });
});

describe('parseWhole', () => {
  it('accepts whole numbers inside the bounds only', () => {
    expect(parseWhole('3', 1, 10)).toEqual({ ok: true, value: 3 });
    expect(parseWhole('0', 1, 10).ok).toBe(false);
    expect(parseWhole('11', 1, 10).ok).toBe(false);
    expect(parseWhole('1.5', 0).ok).toBe(false);
    expect(parseWhole('', 0).ok).toBe(false);
    expect(parseWhole('200', 0)).toEqual({ ok: true, value: 200 });
  });
});

describe('radio ranges', () => {
  it('maps radios to bands per aircraft', () => {
    expect(bandOf('F-16C_50', 'COMM1')).toBe('UHF');
    expect(bandOf('F-16C_50', 'COMM2')).toBe('VHF');
    expect(bandOf('AH-64D_BLK_II', 'FM2')).toBe('FM');
    expect(bandOf('AH-64D_BLK_II', 'HF_TX')).toBe('HF');
    expect(bandOf('AH-64D_BLK_II', 'HF')).toBe('HF');
    expect(bandOf('F-14BU', 'COMM1')).toBeNull();
  });

  it('flags frequencies outside the documented band, edges included as fine', () => {
    expect(BAND_RANGES.UHF).toEqual([225, 399.975]);
    expect(isOutOfRange('F-16C_50', 'COMM1', 251)).toBe(false);
    expect(isOutOfRange('F-16C_50', 'COMM1', 225)).toBe(false);
    expect(isOutOfRange('F-16C_50', 'COMM1', 500)).toBe(true);
    expect(isOutOfRange('F-16C_50', 'COMM2', 127.5)).toBe(false);
    expect(isOutOfRange('AH-64D_BLK_II', 'FM1', 88)).toBe(true);
    expect(isOutOfRange('AH-64D_BLK_II', 'HF_RX', 5.65)).toBe(false);
    expect(isOutOfRange('AH-64D_BLK_II', 'HF_RX', 30)).toBe(true);
    expect(isOutOfRange('F-14BU', 'X', 1)).toBe(false);
  });

  it('notes fractional MHz only for the F-16', () => {
    expect(isUnconfirmedFraction('F-16C_50', 127.5)).toBe(true);
    expect(isUnconfirmedFraction('F-16C_50', 251)).toBe(false);
    expect(isUnconfirmedFraction('AH-64D_BLK_II', 31.5)).toBe(false);
  });
});
