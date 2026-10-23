import { describe, expect, it } from 'vitest';
import {
  DOWNLOADED_GRACE_MS,
  WAIT_TIMEOUT_MS,
  codeSecondsLeft,
  formatBytes,
  formatCountdown,
  parseExpiryMinutes,
  wizardState,
  type WizardInput,
} from './agentWizard';

const NOW = 1_000_000_000;
const base: WizardInput = { available: true, online: false, downloadedAt: null, lastSeen: null, now: NOW };
const at = (overrides: Partial<WizardInput>) => wizardState({ ...base, ...overrides });

describe('wizardState', () => {
  it('is not_built when the installer is unavailable', () => {
    expect(at({ available: false })).toBe('not_built');
  });

  it('is ready before any download, and also while availability is unknown', () => {
    expect(at({})).toBe('ready');
    expect(at({ available: null })).toBe('ready');
  });

  it('goes downloaded -> waiting -> timed_out as time passes', () => {
    expect(at({ downloadedAt: NOW - 1000 })).toBe('downloaded');
    expect(at({ downloadedAt: NOW - DOWNLOADED_GRACE_MS })).toBe('waiting');
    expect(at({ downloadedAt: NOW - WAIT_TIMEOUT_MS + 1 })).toBe('waiting');
    expect(at({ downloadedAt: NOW - WAIT_TIMEOUT_MS })).toBe('timed_out');
  });

  it('is connected as soon as the agent is online, whatever happened before', () => {
    const seen = new Date(NOW - 2000).toISOString();
    expect(at({ online: true, lastSeen: seen })).toBe('connected');
    expect(at({ online: true, lastSeen: seen, downloadedAt: NOW - WAIT_TIMEOUT_MS * 2 })).toBe('connected');
    expect(at({ online: true, lastSeen: seen, available: false })).toBe('connected');
  });

  it('is not connected when online has no last-seen time', () => {
    expect(at({ online: true, lastSeen: null })).toBe('ready');
  });
});

describe('code countdown', () => {
  it('counts down from the download and never goes negative', () => {
    expect(codeSecondsLeft(NOW, 15, NOW)).toBe(900);
    expect(codeSecondsLeft(NOW, 15, NOW + 61_500)).toBe(839);
    expect(codeSecondsLeft(NOW, 15, NOW + 900_000)).toBe(0);
    expect(codeSecondsLeft(NOW, 15, NOW + 5_000_000)).toBe(0);
  });

  it('formats as mm:ss', () => {
    expect(formatCountdown(900)).toBe('15:00');
    expect(formatCountdown(65)).toBe('01:05');
    expect(formatCountdown(0)).toBe('00:00');
    expect(formatCountdown(-5)).toBe('00:00');
  });

  it('reads the expiry header with a 15-minute default', () => {
    expect(parseExpiryMinutes('15')).toBe(15);
    expect(parseExpiryMinutes('30')).toBe(30);
    expect(parseExpiryMinutes(null)).toBe(15);
    expect(parseExpiryMinutes('abc')).toBe(15);
    expect(parseExpiryMinutes('0')).toBe(15);
  });
});

describe('formatBytes', () => {
  it('uses a readable unit', () => {
    expect(formatBytes(512, 'en')).toBe('512 B');
    expect(formatBytes(15 * 1024 * 1024, 'en')).toBe('15 MB');
    expect(formatBytes(1536, 'en')).toBe('1.5 KB');
  });
});
