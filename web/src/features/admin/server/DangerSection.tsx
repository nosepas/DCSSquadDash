import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { deleteServer } from '../../../api/admin';
import type { AdminServer } from '../../../api/types.admin';
import { Card } from '../../../components/Card';
import { Modal } from '../../../components/Modal';
import { ErrorState } from '../../../components/states/ErrorState';
import { useAction } from '../../../hooks/useAction';
import { useServers } from '../../servers/ServerContext';

/** Delete the server; the admin must type its exact name first. */
export function DangerSection({ server }: { server: AdminServer }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const publicList = useServers().list;
  const [open, setOpen] = useState(false);
  const [typed, setTyped] = useState('');
  const action = useAction();

  const close = () => {
    setOpen(false);
    setTyped('');
  };
  const remove = async () => {
    if (await action.run(() => deleteServer(server.server_id))) {
      publicList.reload();
      navigate('/admin');
    }
  };

  return (
    <Card title={t('admin.server.danger.title')} className="card-danger">
      <p className="muted section-intro">{t('admin.server.danger.intro')}</p>
      <button type="button" className="btn btn-danger" onClick={() => setOpen(true)}>{t('admin.server.danger.button')}</button>
      <Modal open={open} title={t('admin.server.danger.confirmTitle')} onClose={close}>
        <label className="field" htmlFor="del-name">
          <span>{t('admin.server.danger.typeName', { name: server.name })}</span>
          <input id="del-name" value={typed} onChange={(e) => setTyped(e.target.value)} autoComplete="off" autoFocus />
        </label>
        {action.error && <ErrorState error={action.error} />}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={close}>{t('common.cancel')}</button>
          <button type="button" className="btn btn-danger" disabled={typed !== server.name || action.busy} onClick={() => void remove()}>
            {t('admin.server.danger.confirm')}
          </button>
        </div>
      </Modal>
    </Card>
  );
}
