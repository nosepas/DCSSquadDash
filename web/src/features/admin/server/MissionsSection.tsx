import { useTranslation } from 'react-i18next';
import { FolderField } from './FolderField';
import { SectionCard } from './SectionCard';
import type { SectionProps } from './sectionTypes';
import { useSettingsSection } from './useSettingsSection';

export function MissionsSection(props: SectionProps) {
  const { t } = useTranslation();
  const f = useSettingsSection('missions', props);
  return (
    <SectionCard title={t('admin.server.missions.title')} intro={t('admin.server.missions.intro')} form={f}>
      <p><span className="tag tag-warn">{t('admin.server.missions.reserved')}</span></p>
      <FolderField
        id="ms-folder"
        label={t('admin.server.missions.folder')}
        help={t('admin.server.missions.folderHelp')}
        value={f.draft.folder}
        onChange={(folder) => f.edit({ folder })}
        detected={props.server.agent.detected.saved_games}
        error={f.errors['settings.missions.folder']}
      />
    </SectionCard>
  );
}
