import { describe, expect, it } from 'vitest';
import { safeNext } from './safeNext';

const BS = '\\';

describe('safeNext', () => {
  it.each(['/ok', '/ok?x=1#y', '/dtc/lists/3'])('allows %s', (p) => expect(safeNext(p)).toBe(p));

  it.each([
    `/${BS}evil.example/x`,
    '//evil.example',
    `/a${BS}b`,
    'https://evil.example',
    'javascript:alert(1)',
    'ok',
    '/ok\nx',
    '/ok\u007f',
    '/\t/evil.example',
    '/' + 'a'.repeat(600),
    '',
    null,
    undefined,
  ])('rejects %j', (p) => expect(safeNext(p)).toBe('/'));

  it('rejects a backslash that is only revealed after decoding', () => {
    // searchParams.get() decodes %5C, so the guard sees the raw backslash.
    const raw = new URLSearchParams('next=/%5Cevil.example/x').get('next');
    expect(raw).toBe(`/${BS}evil.example/x`);
    expect(safeNext(raw)).toBe('/');
  });
});
