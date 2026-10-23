import { describe, expect, it } from 'vitest';
import ca from './ca.json';
import en from './en.json';
import es from './es.json';
import eu from './eu.json';
import gl from './gl.json';

type Tree = { [key: string]: string | Tree };

function flatten(tree: Tree, prefix = ''): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(tree)) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (typeof v === 'string') out[key] = v;
    else Object.assign(out, flatten(v, key));
  }
  return out;
}

const languages: Record<string, Tree> = { es, ca, en, gl, eu };
const reference = flatten(es);
const placeholders = (s: string) => (s.match(/{{\s*\w+\s*}}/g) ?? []).sort().join(',');

describe('i18n catalogues', () => {
  for (const [code, tree] of Object.entries(languages)) {
    const flat = flatten(tree);

    it(`${code} has exactly the same keys as es`, () => {
      expect(Object.keys(flat).sort()).toEqual(Object.keys(reference).sort());
    });

    it(`${code} has no empty values and the same placeholders as es`, () => {
      for (const [key, value] of Object.entries(flat)) {
        expect(value.trim().length, `${code}:${key} is empty`).toBeGreaterThan(0);
        expect(placeholders(value), `${code}:${key} placeholders`).toBe(placeholders(reference[key] ?? ''));
      }
    });
  }
});
