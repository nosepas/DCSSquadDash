import { useTranslation } from 'react-i18next';
import type { AdminServer } from '../../../../api/types.admin';
import { DetectedChips } from '../DetectedChips';
import { StepShell } from './StepShell';

const jump = (section: string) => () => {
  window.location.hash = `sec-${section}`;
};

/** Step 4: the folders the agent found, and where on this page to pick (and save) them. */
export function FoldersStep({ server, connected }: { server: AdminServer; connected: boolean }) {
  const { t } = useTranslation();
  const { detected } = server.agent;
  const found = (detected.foothold_saves?.length ?? 0) + (detected.tacview?.length ?? 0) > 0;
  return (
    <StepShell n={connected ? 1 : 4} id="wz4" title={t('admin.server.wizard.s4.title')} help={t('admin.server.wizard.s4.help')}>
      {!connected ? (
        <p className="muted">{t('admin.server.wizard.s4.idle')}</p>
      ) : (
        <>
          <p><b>{t('admin.server.wizard.s4.cta')}</b></p>
          {found ? (
            <>
              <p className="small muted">{t('admin.server.wizard.s4.found')}</p>
              <p className="wizard-label">{t('admin.server.foothold.title')}</p>
              <DetectedChips items={detected.foothold_saves} current="" onPick={jump('foothold')} />
              <p className="wizard-label">{t('admin.server.tacview.title')}</p>
              <DetectedChips items={detected.tacview} current="" onPick={jump('tacview')} />
            </>
          ) : (
            <p className="notice">{t('admin.server.wizard.s4.none')}</p>
          )}
          <div className="wizard-actions">
            <a className="btn btn-primary" href="#sec-foothold">{t('admin.server.wizard.s4.goFoothold')}</a>
            <a className="btn btn-primary" href="#sec-tacview">{t('admin.server.wizard.s4.goTacview')}</a>
          </div>
        </>
      )}
    </StepShell>
  );
}
