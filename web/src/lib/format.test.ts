import { describe, expect, it } from 'vitest';
import { formatClock, formatKd, kdRatio, percent, remainingSeconds } from './format';

describe('format helpers', () => {
  it('formats a countdown clock and never goes negative', () => {
    expect(formatClock(125)).toBe('02:05');
    expect(formatClock(0)).toBe('00:00');
    expect(formatClock(-9)).toBe('00:00');
  });

  it('computes remaining seconds from an ISO expiry', () => {
    const now = Date.parse('2026-01-01T00:00:00Z');
    expect(remainingSeconds('2026-01-01T00:01:30Z', now)).toBe(90);
    expect(remainingSeconds('2025-12-31T23:59:00Z', now)).toBe(0);
    expect(remainingSeconds('garbage', now)).toBe(0);
  });

  it('computes K/D without dividing by zero', () => {
    expect(kdRatio(10, 4)).toBe(2.5);
    expect(kdRatio(7, 0)).toBe(7);
    expect(formatKd(2)).toBe('2.00');
  });

  it('computes percentages safely', () => {
    expect(percent(5, 20)).toBe(25);
    expect(percent(1, 0)).toBe(0);
  });
});
