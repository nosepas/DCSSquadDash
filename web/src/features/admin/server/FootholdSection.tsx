import { useTranslation } from 'react-i18next';
import { ToggleField } from '../../../components/form/ToggleField';
import { FolderField } from './FolderField';
import { SectionCard } from './SectionCard';
import type { SectionProps } from './sectionTypes';
import { useSettingsSection } from './useSettingsSection';

export function FootholdSection(props: SectionProps) {
  const { t } = useTranslation();
  const f = useSettingsSection('foothold', props);
  return (
    <SectionCard title={t('admin.server.foothold.title')} intro={t('admin.server.foothold.intro')} form={f}>
      <ToggleField id="fh-enabled" label={t('admin.server.foothold.enabled')} help={t('admin.server.foothold.enabledHelp')} checked={f.draft.enabled} onChange={(enabled) => f.edit({ enabled })} />
      <FolderField
        id="fh-dir"
        label={t('admin.server.foothold.dir')}
        help={t('admin.server.foothold.dirHelp')}
        value={f.draft.saves_dir}
        onChange={(saves_dir) => f.edit({ saves_dir })}
        detected={props.server.agent.detected.foothold_saves}
        error={f.errors['settings.foothold.saves_dir']}
      />
    </SectionCard>
  );
}
