import { useTranslation } from 'react-i18next';
import { StepShell } from './StepShell';

const range = (n: number) => Array.from({ length: n }, (_, i) => i + 1);

/** The main causes when the agent does not connect (shared by step 2 and the timeout hint of step 3). */
export function Problems() {
  const { t } = useTranslation();
  return (
    <ul className="wizard-list">
      {range(4).map((i) => <li key={i}>{t(`admin.server.wizard.s2.p${i}`)}</li>)}
    </ul>
  );
}

/** Step 2: static, numbered instructions for the DCS server PC, plus two collapsible explanations. */
export function InstallStep() {
  const { t } = useTranslation();
  return (
    <StepShell n={2} id="wz2" title={t('admin.server.wizard.s2.title')} help={t('admin.server.wizard.s2.help')}>
      <ol className="wizard-sub">
        {range(5).map((i) => (
          <li key={i}>
            <b>{t(`admin.server.wizard.s2.step${i}`)}</b>
            <span className="muted small">{t(`admin.server.wizard.s2.hint${i}`)}</span>
          </li>
        ))}
      </ol>
      <details className="wizard-details">
        <summary>{t('admin.server.wizard.s2.whatTitle')}</summary>
        <ul className="wizard-list">
          {range(4).map((i) => <li key={i}>{t(`admin.server.wizard.s2.what${i}`)}</li>)}
        </ul>
      </details>
      <details className="wizard-details">
        <summary>{t('admin.server.wizard.s2.problemsTitle')}</summary>
        <Problems />
      </details>
    </StepShell>
  );
}
