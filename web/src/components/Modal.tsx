import { useEffect, useRef, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

interface Props {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

/** Accessible modal built on the native <dialog> (focus trap, Esc to close, inert background). */
export function Modal({ open, title, onClose, children }: Props) {
  const { t } = useTranslation();
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dlg = ref.current;
    if (!dlg) return;
    if (open && !dlg.open) dlg.showModal();
    if (!open && dlg.open) dlg.close();
  }, [open]);

  return (
    <dialog ref={ref} className="modal" aria-labelledby="modal-title" onClose={onClose}>
      {open && (
        <div className="modal-body">
          <header className="modal-head">
            <h2 id="modal-title">{title}</h2>
            <button type="button" className="btn btn-ghost" onClick={onClose} aria-label={t('common.close')}>
              ✕
            </button>
          </header>
          {children}
        </div>
      )}
    </dialog>
  );
}
