import { useTranslation } from 'react-i18next';
import { packageErrorKey } from '../../../../api/agentPackage';
import { Loading } from '../../../../components/states/Loading';
import { DEFAULT_CODE_MINUTES, codeSecondsLeft, formatBytes, formatCountdown } from '../../../../lib/agentWizard';
import { AGENT_BUILD_COMMAND } from './constants';
import { StepShell } from './StepShell';
import type { AgentPackage } from './useAgentPackage';

interface Props {
  pkg: AgentPackage;
  now: number;
  notBuilt: boolean;
}

/** Step 1: the big download button, what the file is, and the live validity of its one-time code. */
export function DownloadStep({ pkg, now, notBuilt }: Props) {
  const { t, i18n } = useTranslation();
  const { info, memory } = pkg;
  const left = memory ? codeSecondsLeft(memory.at, memory.minutes, now) : 0;
  const meta = [
    info?.version ? t('admin.server.wizard.dl.version', { version: info.version }) : null,
    info?.size_bytes ? formatBytes(info.size_bytes, i18n.language) : null,
  ].filter(Boolean).join(' · ');
  const label = pkg.busy ? 'busy' : memory ? 'again' : 'button';
  return (
    <StepShell n={1} id="wz1" title={t('admin.server.wizard.s1.title')} help={t('admin.server.wizard.s1.help')}>
      <p>{t('admin.server.wizard.s1.what')}</p>
      <ul className="wizard-list">
        {[1, 2, 3].map((i) => <li key={i}>{t(`admin.server.wizard.s1.safe${i}`)}</li>)}
      </ul>
      {notBuilt ? (
        <div className="notice notice-warn" role="status">
          <p><b>{t('admin.server.wizard.nb.title')}</b></p>
          <p>{t('admin.server.wizard.nb.body')}</p>
          <pre className="cmd mono">{AGENT_BUILD_COMMAND}</pre>
          <button type="button" className="btn" onClick={pkg.reloadInfo}>{t('admin.server.wizard.nb.check')}</button>
        </div>
      ) : (
        <>
          {pkg.infoLoading && !info && <Loading />}
          <div className="wizard-actions">
            <button type="button" className="btn btn-primary btn-lg" onClick={() => void pkg.download()} disabled={pkg.busy}>
              {t(`admin.server.wizard.dl.${label}`)}
            </button>
            {meta && <span className="muted small">{meta}</span>}
          </div>
          <p className="field-help">{t('admin.server.wizard.dl.code', { minutes: memory?.minutes ?? DEFAULT_CODE_MINUTES })}</p>
        </>
      )}
      {pkg.error && <p className="field-error" role="alert">{t(`admin.server.wizard.errors.${packageErrorKey(pkg.error)}`)}</p>}
      {memory && !notBuilt && (
        <div className={`notice ${left > 0 ? '' : 'notice-warn'}`} role="status">
          <p>{t('admin.server.wizard.dl.started', { name: memory.filename })}</p>
          <p>
            {left > 0
              ? <>{t('admin.server.wizard.dl.countdown')}: <b className="mono">{formatCountdown(left)}</b></>
              : t('admin.server.wizard.dl.expired')}
          </p>
        </div>
      )}
    </StepShell>
  );
}
