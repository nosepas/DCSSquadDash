import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/Card';
import { errorKey } from '../../../lib/errors';
import type { SectionForm } from './useSectionForm';

interface Props {
  title: string;
  intro?: string;
  form: SectionForm;
  children: ReactNode;
}

/** A titled settings section with its own Save button and success/error feedback. */
export function SectionCard({ title, intro, form, children }: Props) {
  const { t } = useTranslation();
  const err = form.error;
  const message = err && (err.status === 422 ? t('admin.server.saveError') : t(`errors.${errorKey(err)}`));
  return (
    <Card title={title}>
      <form onSubmit={(e) => void form.submit(e)} noValidate>
        {intro && <p className="muted section-intro">{intro}</p>}
        {children}
        <div className="section-foot">
          <button type="submit" className="btn btn-primary" disabled={form.busy || !form.dirty}>
            {t('common.save')}
          </button>
          {form.dirty && <span className="tag tag-warn">{t('common.dirty')}</span>}
          {form.ok && <span className="tag tag-ok" role="status">{t('common.saved')}</span>}
          {message && <span className="field-error" role="alert">{message}</span>}
        </div>
      </form>
    </Card>
  );
}
