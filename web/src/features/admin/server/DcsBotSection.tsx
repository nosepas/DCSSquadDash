import { useTranslation } from 'react-i18next';
import { TextField } from '../../../components/form/TextField';
import { ToggleField } from '../../../components/form/ToggleField';
import { SectionCard } from './SectionCard';
import type { SectionProps } from './sectionTypes';
import { useSettingsSection } from './useSettingsSection';

export function DcsBotSection(props: SectionProps) {
  const { t } = useTranslation();
  const f = useSettingsSection('dcsbot', props);
  const e = f.errors;
  const detected = props.server.agent.detected.dcsserverbot ?? [];
  const k = (name: string) => t(`admin.server.dcsbot.${name}`);
  return (
    <SectionCard title={k('title')} intro={k('intro')} form={f}>
      <div className="notice notice-warn" role="note">
        <p>{k('secrets')}</p>
        <p className="mono small">{k('secretsWhere')}</p>
      </div>
      {detected.length > 0 && (
        <p className="muted small">
          {k('detected')}: {detected.map((d) => <span key={d.path} className="mono">{d.path} </span>)}
        </p>
      )}
      <ToggleField id="bot-rest" label={k('restEnabled')} help={k('restEnabledHelp')} checked={f.draft.rest_enabled} onChange={(rest_enabled) => f.edit({ rest_enabled })} />
      <TextField id="bot-url" label={k('restUrl')} help={k('restUrlHelp')} error={e['settings.dcsbot.rest_url']} mono value={f.draft.rest_url} onChange={(rest_url) => f.edit({ rest_url })} />
      <TextField id="bot-prefix" label={k('restPrefix')} help={k('restPrefixHelp')} error={e['settings.dcsbot.rest_prefix']} mono value={f.draft.rest_prefix} onChange={(rest_prefix) => f.edit({ rest_prefix })} />
      <TextField id="bot-name" label={k('serverName')} help={k('serverNameHelp')} error={e['settings.dcsbot.server_name']} value={f.draft.server_name ?? ''} onChange={(v) => f.edit({ server_name: v === '' ? null : v })} />
      <ToggleField id="bot-db" label={k('dbEnabled')} help={k('dbEnabledHelp')} checked={f.draft.db_enabled} onChange={(db_enabled) => f.edit({ db_enabled })} />
    </SectionCard>
  );
}
