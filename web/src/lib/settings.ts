import type { ServerSettings, SettingsKey } from '../api/types.admin';

/** The API replaces `settings` as a whole, so editing one section must carry every other one untouched. */
export function mergeSection<K extends SettingsKey>(settings: ServerSettings, key: K, value: ServerSettings[K]): ServerSettings {
  return { ...settings, [key]: value };
}

/** Empty text inputs are stored as null, never as an empty string. */
export function blankToNull(v: string | null | undefined): string | null {
  const t = (v ?? '').trim();
  return t === '' ? null : t;
}

export function isDirty(saved: unknown, draft: unknown): boolean {
  return JSON.stringify(saved) !== JSON.stringify(draft);
}
