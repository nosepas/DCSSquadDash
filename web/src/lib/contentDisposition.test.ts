import { describe, expect, it } from 'vitest';
import { parseContentDisposition } from './contentDisposition';

describe('parseContentDisposition', () => {
  it('reads quoted and unquoted filenames', () => {
    expect(parseContentDisposition('attachment; filename="FOX3-Agent-Demo.zip"', 'x.zip')).toBe('FOX3-Agent-Demo.zip');
    expect(parseContentDisposition('attachment; filename=agent.zip', 'x.zip')).toBe('agent.zip');
    expect(parseContentDisposition('attachment; filename="a b; c.zip"', 'x.zip')).toBe('a b; c.zip');
  });

  it('prefers the UTF-8 filename* form', () => {
    expect(parseContentDisposition("attachment; filename*=UTF-8''FOX3%20Ag%C3%A9nt.zip", 'x.zip')).toBe('FOX3 Agént.zip');
    expect(parseContentDisposition('attachment; filename="plain.zip"; filename*=UTF-8\'\'fancy%E2%9C%93.zip', 'x.zip')).toBe('fancy✓.zip');
  });

  it('falls back when the header is missing, empty or unusable', () => {
    expect(parseContentDisposition(null, 'FOX3-Agent.zip')).toBe('FOX3-Agent.zip');
    expect(parseContentDisposition('attachment', 'FOX3-Agent.zip')).toBe('FOX3-Agent.zip');
    expect(parseContentDisposition("attachment; filename*=UTF-8''%E0%A4%A", 'FOX3-Agent.zip')).toBe('FOX3-Agent.zip');
  });

  it('never lets the header choose a directory', () => {
    expect(parseContentDisposition('attachment; filename="..\\\\..\\\\evil.zip"', 'x.zip')).toBe('evil.zip');
    expect(parseContentDisposition('attachment; filename="/etc/passwd"', 'x.zip')).toBe('passwd');
    expect(parseContentDisposition('attachment; filename=".."', 'x.zip')).toBe('x.zip');
  });
});
