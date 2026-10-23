import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { AdminServer } from '../../../../api/types.admin';
import { Card } from '../../../../components/Card';
import { useNow } from '../../../../hooks/useNow';
import { wizardState } from '../../../../lib/agentWizard';
import { relativeTime } from '../../../../lib/time';
import { DownloadStep } from './DownloadStep';
import { FoldersStep } from './FoldersStep';
import { GuidePanel } from './GuidePanel';
import { InstallStep } from './InstallStep';
import { useAgentPackage } from './useAgentPackage';
import { useAgentPoll } from './useAgentPoll';
import { WaitStep } from './WaitStep';

interface Props {
  server: AdminServer;
  apply: (server: AdminServer) => void;
}

/** Guided "connect an agent" wizard: download the installer, run it on the DCS PC, wait, pick the folders. */
export function AgentWizard({ server, apply }: Props) {
  const { t, i18n } = useTranslation();
  const now = useNow(1000);
  const pkg = useAgentPackage(server.server_id);
  const [guide, setGuide] = useState(false);
  const state = wizardState({
    available: pkg.info ? pkg.info.available : null,
    online: server.online,
    downloadedAt: pkg.memory?.at ?? null,
    lastSeen: server.agent.last_seen,
    now,
  });
  const connected = state === 'connected';
  useAgentPoll(server.server_id, state === 'downloaded' || state === 'waiting' || state === 'timed_out', apply);
  const download = <DownloadStep pkg={pkg} now={now} notBuilt={state === 'not_built'} />;
  return (
    <Card
      title={t('admin.server.wizard.title')}
      className="wizard"
      actions={
        <button type="button" className="btn" aria-expanded={guide} aria-controls="wizard-guide" onClick={() => setGuide((g) => !g)}>
          {guide ? t('admin.server.wizard.hideGuide') : t('admin.server.wizard.showGuide')}
        </button>
      }
    >
      <p className="muted section-intro">{t('admin.server.wizard.help')}</p>
      {guide && <GuidePanel onClose={() => setGuide(false)} />}
      {connected && (
        <div className="wizard-done" role="status">
          <span className="wizard-check" aria-hidden="true">✓</span>
          <div>
            <b>{t('admin.server.wizard.done.title')}</b>
            <p className="muted small">
              {t('admin.server.wizard.done.info', { version: server.agent.version ?? '–', seen: relativeTime(server.agent.last_seen, now, i18n.language) })}
            </p>
          </div>
        </div>
      )}
      <ol className="wizard-steps">
        {connected ? (
          <>
            <FoldersStep server={server} connected />
            <li className="wizard-more">
              <details className="wizard-details">
                <summary>{t('admin.server.wizard.done.more')}</summary>
                <p className="notice">{t('admin.server.wizard.done.moveNote')}</p>
                <ol className="wizard-steps">{download}<InstallStep /></ol>
              </details>
            </li>
          </>
        ) : (
          <>
            {download}
            <InstallStep />
            <WaitStep state={state} server={server} />
            <FoldersStep server={server} connected={false} />
          </>
        )}
      </ol>
    </Card>
  );
}
