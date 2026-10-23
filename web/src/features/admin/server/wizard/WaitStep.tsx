import { useTranslation } from 'react-i18next';
import type { AdminServer } from '../../../../api/types.admin';
import type { WizardState } from '../../../../lib/agentWizard';
import { WarningList } from '../WarningList';
import { Problems } from './InstallStep';
import { StepShell } from './StepShell';

interface Props {
  state: WizardState;
  server: AdminServer;
}

/** Step 3: live waiting indicator; after 3 minutes without a connection it expands the troubleshooting hints. */
export function WaitStep({ state, server }: Props) {
  const { t } = useTranslation();
  const waiting = state === 'downloaded' || state === 'waiting' || state === 'timed_out';
  return (
    <StepShell n={3} id="wz3" title={t('admin.server.wizard.s3.title')} help={t('admin.server.wizard.s3.help')}>
      {waiting ? (
        <div className="wizard-wait" role="status" aria-live="polite">
          <span className="spinner" aria-hidden="true" />
          <div>
            <b>{t('admin.server.wizard.s3.waiting')}</b>
            <p className="muted small">{t('admin.server.wizard.s3.waitingHelp')}</p>
          </div>
        </div>
      ) : (
        <p className="muted">{t('admin.server.wizard.s3.idle')}</p>
      )}
      {state === 'timed_out' && (
        <div className="notice notice-warn" role="alert">
          <p><b>{t('admin.server.wizard.s3.timeoutTitle')}</b></p>
          <p>{t('admin.server.wizard.s3.timeoutBody')}</p>
          <Problems />
        </div>
      )}
      {waiting && server.agent.warnings.length > 0 && <WarningList warnings={server.agent.warnings} />}
    </StepShell>
  );
}
