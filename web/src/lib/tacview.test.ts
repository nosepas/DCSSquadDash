import { describe, expect, it } from 'vitest';
import { downloadErrorKey, filenameFromDisposition, formatOffset, formatUtc } from './tacview';

describe('tacview helpers', () => {
  it('formats offsets as HH:MM:SS', () => {
    expect(formatOffset(0)).toBe('00:00:00');
    expect(formatOffset(120)).toBe('00:02:00');
    expect(formatOffset(3600.5)).toBe('01:00:00');
    expect(formatOffset(3 * 3600 + 25 * 60 + 9)).toBe('03:25:09');
    expect(formatOffset(100 * 3600)).toBe('100:00:00');
    expect(formatOffset(-5)).toBe('00:00:00');
    expect(formatOffset(Number.NaN)).toBe('00:00:00');
  });

  it('formats UTC timestamps', () => {
    expect(formatUtc('2026-03-01T18:02:00Z')).toBe('2026-03-01 18:02:00');
    expect(formatUtc(null)).toBe('–');
  });

  it('maps download failures to message keys', () => {
    expect(downloadErrorKey(504, 'server_unreachable')).toBe('server_unreachable');
    expect(downloadErrorKey(404, 'not_found')).toBe('not_found');
    expect(downloadErrorKey(429, 'transfer_busy')).toBe('transfer_busy');
    expect(downloadErrorKey(0, 'network')).toBe('network');
    expect(downloadErrorKey(500, 'x')).toBe('generic');
  });

  it('reads the file name from Content-Disposition', () => {
    expect(filenameFromDisposition('attachment; filename="Tacview-1.zip.acmi"', 'x')).toBe('Tacview-1.zip.acmi');
    expect(filenameFromDisposition(null, 'fallback.acmi')).toBe('fallback.acmi');
  });
});
