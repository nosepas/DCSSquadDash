/** Every agent warning code the admin panel can explain; each has `warnings.<CODE>.title` and `.fix` translations. */
export const WARNING_CODES = [
  'FOOTHOLD_FILE_STALE',
  'FOOTHOLD_FOLDER_MISSING',
  'FOOTHOLD_FILE_MISSING',
  'FOOTHOLD_FILE_UNREADABLE',
  'FOOTHOLD_FILE_INVALID',
  'FOOTHOLD_FOLDER_NOT_SET',
  'DCSBOT_UNREACHABLE',
  'DCSBOT_AUTH_FAILED',
  'DCSBOT_SERVER_NOT_FOUND',
  'DCSBOT_DB_ERROR',
  'DCSBOT_UCID_UNRESOLVED',
  'DCSBOT_CONFIG_INVALID',
  'TACVIEW_FOLDER_MISSING',
  'TACVIEW_FOLDER_UNREADABLE',
  'TACVIEW_FILE_FAILED',
  'TACVIEW_FORMAT_UNSUPPORTED',
  'TACVIEW_INDEXING',
  'TACVIEW_APPEARANCES_CAPPED',
  'SOURCE_CRASHED',
  'CENTRAL_REJECTED_MESSAGES',
] as const;

export type WarningCode = (typeof WARNING_CODES)[number];

export function isKnownWarning(code: string): code is WarningCode {
  return (WARNING_CODES as readonly string[]).includes(code);
}

/** Translation keys for a warning, or null when the code is unknown (the UI then shows the raw code and message). */
export function warningKeys(code: string): { title: string; fix: string } | null {
  return isKnownWarning(code) ? { title: `warnings.${code}.title`, fix: `warnings.${code}.fix` } : null;
}
