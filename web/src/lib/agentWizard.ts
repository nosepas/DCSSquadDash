import { formatClock } from './format';

/** How long the personalised installer's one-time code is valid when the server does not say. */
export const DEFAULT_CODE_MINUTES = 15;
/** Without a connection after this long, the wizard expands its troubleshooting hints. */
export const WAIT_TIMEOUT_MS = 3 * 60_000;
/** Right after a download the wizard shows a "download started" confirmation for this long. */
export const DOWNLOADED_GRACE_MS = 10_000;
/** The status of the agent is polled this often while the waiting step is open. */
export const POLL_MS = 3000;

export type WizardState = 'not_built' | 'ready' | 'downloaded' | 'waiting' | 'connected' | 'timed_out';

export interface WizardInput {
  /** From `agent-package`; null while it is still loading or when it could not be read. */
  available: boolean | null;
  online: boolean;
  /** When this browser downloaded the installer (ms epoch), or null. */
  downloadedAt: number | null;
  lastSeen: string | null;
  now: number;
}

/** Which stage of "connect an agent" the admin is in. A live agent always wins; unknown availability allows a try. */
export function wizardState({ available, online, downloadedAt, lastSeen, now }: WizardInput): WizardState {
  if (online && lastSeen !== null) return 'connected';
  if (available === false) return 'not_built';
  if (downloadedAt === null) return 'ready';
  const elapsed = now - downloadedAt;
  if (elapsed < DOWNLOADED_GRACE_MS) return 'downloaded';
  return elapsed >= WAIT_TIMEOUT_MS ? 'timed_out' : 'waiting';
}

/** Whole seconds until the one-time code stops working (0 once expired). */
export function codeSecondsLeft(downloadedAt: number, validMinutes: number, now: number): number {
  return Math.max(0, Math.ceil((downloadedAt + validMinutes * 60_000 - now) / 1000));
}

/** "14:59" style countdown. */
export const formatCountdown = (seconds: number): string => formatClock(seconds);

export function parseExpiryMinutes(header: string | null): number {
  const n = Number(header);
  return Number.isFinite(n) && n > 0 ? n : DEFAULT_CODE_MINUTES;
}

/** Human size like "14.2 MB". */
export function formatBytes(bytes: number, locale: string): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  const nf = new Intl.NumberFormat(locale, { maximumFractionDigits: i === 0 ? 0 : 1 });
  return `${nf.format(value)} ${units[i]}`;
}
