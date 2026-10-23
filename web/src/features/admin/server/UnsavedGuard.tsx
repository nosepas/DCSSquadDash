import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ConfirmDialog } from '../../../components/ConfirmDialog';

/** Warns before leaving the page (in-app navigation and tab close/reload) while there are unsaved edits. */
export function UnsavedGuard({ active }: { active: boolean }) {
  const { t } = useTranslation();
  const blocker = useBlocker(({ currentLocation, nextLocation }) => active && currentLocation.pathname !== nextLocation.pathname);

  useEffect(() => {
    if (!active) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [active]);

  return (
    <ConfirmDialog
      open={blocker.state === 'blocked'}
      title={t('admin.server.unsaved.title')}
      message={t('admin.server.unsaved.message')}
      confirmLabel={t('admin.server.unsaved.leave')}
      cancelLabel={t('admin.server.unsaved.stay')}
      onConfirm={() => blocker.state === 'blocked' && blocker.proceed()}
      onCancel={() => blocker.state === 'blocked' && blocker.reset()}
    />
  );
}
