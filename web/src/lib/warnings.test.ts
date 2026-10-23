import { describe, expect, it } from 'vitest';
import es from '../i18n/es.json';
import { WARNING_CODES, warningKeys } from './warnings';

const warnings = (es as unknown as { warnings: Record<string, { title?: string; fix?: string }> }).warnings;

describe('warning codes', () => {
  it('covers every code listed by the agent', () => {
    expect(WARNING_CODES).toHaveLength(20);
  });

  it('has a title and a fix translation for every known code', () => {
    for (const code of WARNING_CODES) {
      expect(warningKeys(code)?.title).toBe(`warnings.${code}.title`);
      expect(warnings[code]?.title, code).toBeTruthy();
      expect(warnings[code]?.fix, code).toBeTruthy();
    }
  });

  it('returns null for unknown codes so the UI can show them raw', () => {
    expect(warningKeys('SOMETHING_NEW')).toBeNull();
  });
});
