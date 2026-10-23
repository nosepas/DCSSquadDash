import { describe, expect, it } from 'vitest';
import { relativeTime } from './time';

describe('relativeTime', () => {
  const now = Date.parse('2026-01-01T12:00:00Z');

  it('describes recent and old timestamps', () => {
    expect(relativeTime('2026-01-01T11:59:30Z', now, 'en')).toBe('30 seconds ago');
    expect(relativeTime('2026-01-01T11:55:00Z', now, 'en')).toBe('5 minutes ago');
    expect(relativeTime('2025-12-30T12:00:00Z', now, 'en')).toBe('2 days ago');
  });

  it('shows a dash for missing values', () => {
    expect(relativeTime(null, now, 'en')).toBe('–');
    expect(relativeTime('garbage', now, 'en')).toBe('–');
  });
});
