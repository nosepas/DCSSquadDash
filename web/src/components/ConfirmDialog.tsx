import { useTranslation } from 'react-i18next';
import { Modal } from './Modal';

interface Props {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({ open, title, message, confirmLabel, cancelLabel, busy, onConfirm, onCancel }: Props) {
  const { t } = useTranslation();
  return (
    <Modal open={open} title={title} onClose={onCancel}>
      <p>{message}</p>
      <div className="modal-actions">
        <button type="button" className="btn" onClick={onCancel} autoFocus>
          {cancelLabel ?? t('common.cancel')}
        </button>
        <button type="button" className="btn btn-danger" onClick={onConfirm} disabled={busy}>
          {confirmLabel ?? t('common.confirm')}
        </button>
      </div>
    </Modal>
  );
}
