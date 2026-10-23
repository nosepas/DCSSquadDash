import { useTranslation } from 'react-i18next';
import { updateServer } from '../../../api/admin';
import type { MissionType } from '../../../api/types';
import type { GeneralFields } from '../../../api/types.admin';
import { describedBy, FieldShell } from '../../../components/form/FieldShell';
import { TextField } from '../../../components/form/TextField';
import { ToggleField } from '../../../components/form/ToggleField';
import { blankToNull } from '../../../lib/settings';
import { SectionCard } from './SectionCard';
import type { SectionProps } from './sectionTypes';
import { useSectionForm } from './useSectionForm';

export function GeneralSection({ server, apply }: SectionProps) {
  const { t } = useTranslation();
  const saved: GeneralFields = {
    name: server.name,
    mission_type: server.mission_type,
    address: server.address,
    description: server.description,
    enabled: server.enabled,
  };
  const f = useSectionForm('general', saved, async (d) => {
    const body = { ...d, name: d.name.trim(), address: blankToNull(d.address), description: blankToNull(d.description) };
    apply(await updateServer(server.server_id, body));
  });
  const k = (name: string) => t(`admin.server.general.${name}`);
  const typeHelp = k('typeHelp');
  return (
    <SectionCard title={k('title')} intro={k('intro')} form={f}>
      <TextField id="gen-name" label={k('name')} help={k('nameHelp')} error={f.errors.name} value={f.draft.name} maxLength={80} required onChange={(name) => f.edit({ name })} />
      <FieldShell id="gen-type" label={k('type')} help={typeHelp} error={f.errors.mission_type}>
        <select id="gen-type" value={f.draft.mission_type} aria-describedby={describedBy('gen-type', typeHelp, f.errors.mission_type)} onChange={(e) => f.edit({ mission_type: e.target.value as MissionType })}>
          <option value="foothold">{t('missionType.foothold')}</option>
          <option value="generic">{t('missionType.generic')}</option>
        </select>
      </FieldShell>
      <TextField id="gen-address" label={k('address')} help={k('addressHelp')} error={f.errors.address} mono placeholder="203.0.113.5:10308" value={f.draft.address ?? ''} onChange={(v) => f.edit({ address: v === '' ? null : v })} />
      <TextField id="gen-desc" label={k('description')} help={k('descriptionHelp')} error={f.errors.description} multiline maxLength={500} optional={t('common.optional')} value={f.draft.description ?? ''} onChange={(v) => f.edit({ description: v === '' ? null : v })} />
      <ToggleField id="gen-enabled" label={k('enabled')} help={k('enabledHelp')} checked={f.draft.enabled} onChange={(enabled) => f.edit({ enabled })} />
    </SectionCard>
  );
}
