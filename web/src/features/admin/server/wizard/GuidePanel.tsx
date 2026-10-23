import { useTranslation } from 'react-i18next';

const SECTIONS = [1, 2, 3, 4, 5, 6];

/** In-page "full guide" (same content as docs/ADMINISTRADOR-AGENT.md, condensed). */
export function GuidePanel({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  return (
    <section id="wizard-guide" className="wizard-guide" aria-labelledby="wizard-guide-title">
      <header className="wizard-guide-head">
        <h3 id="wizard-guide-title">{t('admin.server.wizard.guide.title')}</h3>
        <button type="button" className="btn btn-ghost" onClick={onClose}>{t('admin.server.wizard.hideGuide')}</button>
      </header>
      <p className="muted">{t('admin.server.wizard.guide.intro')}</p>
      {SECTIONS.map((i) => (
        <div key={i}>
          <h4>{t(`admin.server.wizard.guide.g${i}t`)}</h4>
          <p>{t(`admin.server.wizard.guide.g${i}`)}</p>
        </div>
      ))}
    </section>
  );
}
