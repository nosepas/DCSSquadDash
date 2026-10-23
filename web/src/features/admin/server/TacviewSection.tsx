import { useTranslation } from 'react-i18next';
import { ToggleField } from '../../../components/form/ToggleField';
import { FolderField } from './FolderField';
import { SectionCard } from './SectionCard';
import type { SectionProps } from './sectionTypes';
import { useSettingsSection } from './useSettingsSection';

export function TacviewSection(props: SectionProps) {
  const { t } = useTranslation();
  const f = useSettingsSection('tacview', props);
  return (
    <SectionCard title={t('admin.server.tacview.title')} intro={t('admin.server.tacview.intro')} form={f}>
      <ToggleField id="tv-enabled" label={t('admin.server.tacview.enabled')} help={t('admin.server.tacview.enabledHelp')} checked={f.draft.enabled} onChange={(enabled) => f.edit({ enabled })} />
      <FolderField
        id="tv-folder"
        label={t('admin.server.tacview.folder')}
        help={t('admin.server.tacview.folderHelp')}
        value={f.draft.folder}
        onChange={(folder) => f.edit({ folder })}
        detected={props.server.agent.detected.tacview}
        error={f.errors['settings.tacview.folder']}
      />
    </SectionCard>
  );
}
