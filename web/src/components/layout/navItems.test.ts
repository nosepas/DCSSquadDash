import { describe, expect, it } from 'vitest';
import { NAV_ITEMS, visibleNav } from './navItems';

const routes = (ctx: Parameters<typeof visibleNav>[1]) => visibleNav(NAV_ITEMS, ctx).map((i) => i.to);

describe('visibleNav', () => {
  it('shows only the public sections when logged out', () => {
    expect(routes({ authed: false, isAdmin: false, missionType: 'foothold' })).toEqual(['/map', '/missions']);
  });

  it('hides admin from normal users and foothold sections on generic servers', () => {
    expect(routes({ authed: true, isAdmin: false, missionType: 'foothold' })).not.toContain('/admin');
    expect(routes({ authed: true, isAdmin: true, missionType: 'generic' })).toEqual([
      '/map', '/missions', '/tacview', '/dtc', '/players', '/profile', '/admin',
    ]);
  });
});
