import { updateServer } from '../../../api/admin';
import type { ServerSettings, SettingsKey } from '../../../api/types.admin';
import { mergeSection } from '../../../lib/settings';
import type { SectionProps } from './sectionTypes';
import { useSectionForm } from './useSectionForm';

/** One section of `settings`: edits only that part and always sends the complete settings object. */
export function useSettingsSection<K extends SettingsKey>(key: K, { server, apply }: SectionProps) {
  return useSectionForm<ServerSettings[K]>(`settings.${key}`, server.settings[key], async (draft) => {
    apply(await updateServer(server.server_id, { settings: mergeSection(server.settings, key, draft) }));
  });
}
