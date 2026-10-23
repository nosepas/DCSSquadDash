import type { AdminServer } from '../../../api/types.admin';

export interface SectionProps {
  server: AdminServer;
  /** Swap in the fresh server returned by a successful save. */
  apply: (server: AdminServer) => void;
}
