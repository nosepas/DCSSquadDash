import type { MissionType } from '../../api/types';

export interface NavItem {
  to: string;
  labelKey: string;
  /** Needs a logged-in user. Only the map and missions are public. */
  private: boolean;
  admin?: boolean;
  /** Hidden for generic (non-Foothold) servers. */
  footholdOnly?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', labelKey: 'nav.dashboard', private: true, footholdOnly: true },
  { to: '/map', labelKey: 'nav.map', private: false },
  { to: '/missions', labelKey: 'nav.missions', private: false },
  { to: '/objectives', labelKey: 'nav.objectives', private: true, footholdOnly: true },
  { to: '/ranking', labelKey: 'nav.ranking', private: true, footholdOnly: true },
  { to: '/kills', labelKey: 'nav.kills', private: true, footholdOnly: true },
  { to: '/tacview', labelKey: 'nav.tacview', private: true },
  { to: '/dtc', labelKey: 'nav.dtc', private: true },
  { to: '/players', labelKey: 'nav.players', private: true },
  { to: '/profile', labelKey: 'nav.profile', private: true },
  { to: '/admin', labelKey: 'nav.admin', private: true, admin: true },
];

interface Context {
  authed: boolean;
  isAdmin: boolean;
  missionType: MissionType | undefined;
}

export function visibleNav(items: NavItem[], ctx: Context): NavItem[] {
  return items.filter((i) => {
    if (i.private && !ctx.authed) return false;
    if (i.admin && !ctx.isAdmin) return false;
    if (i.footholdOnly && ctx.missionType === 'generic') return false;
    return true;
  });
}
