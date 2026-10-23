import type { Agent } from '../../api/types';

export function agentState(a: Agent): 'revoked' | 'pending' | 'active' {
  if (a.revoked_at) return 'revoked';
  return a.last_seen_at ? 'active' : 'pending';
}
