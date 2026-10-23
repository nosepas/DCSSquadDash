import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createServer } from '../../api/admin';
import type { MissionType } from '../../api/types';
import { FieldShell } from '../../components/form/FieldShell';
import { TextField } from '../../components/form/TextField';
import { Modal } from '../../components/Modal';
import { ErrorState } from '../../components/states/ErrorState';
import { useAction } from '../../hooks/useAction';
import { fieldErrors } from '../../lib/fieldErrors';

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

/** "New server": name + type, then straight to the server's detail page to configure the rest. */
export function NewServerDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [type, setType] = useState<MissionType>('foothold');
  const { busy, error, run, clear } = useAction();

  useEffect(() => {
    if (open) {
      setName('');
      setType('foothold');
      clear();
    }
  }, [open, clear]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    let id = '';
    if (await run(async () => (id = (await createServer(name.trim(), type)).server_id))) {
      onCreated();
      navigate(`/admin/servers/${id}`);
    }
  };

  const errors = fieldErrors(error);
  return (
    <Modal open={open} title={t('admin.servers.newTitle')} onClose={onClose}>
      <form onSubmit={(e) => void submit(e)} className="form">
        <p className="muted">{t('admin.servers.newIntro')}</p>
        <TextField id="new-name" label={t('admin.server.general.name')} help={t('admin.server.general.nameHelp')} error={errors.name} placeholder={t('admin.servers.namePlaceholder')} maxLength={80} required value={name} onChange={setName} />
        <FieldShell id="new-type" label={t('admin.server.general.type')} help={t('admin.server.general.typeHelp')}>
          <select id="new-type" value={type} onChange={(e) => setType(e.target.value as MissionType)}>
            <option value="foothold">{t('missionType.foothold')}</option>
            <option value="generic">{t('missionType.generic')}</option>
          </select>
        </FieldShell>
        {error && !errors.name && <ErrorState error={error} />}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>{t('common.cancel')}</button>
          <button type="submit" className="btn btn-primary" disabled={busy || name.trim() === ''}>{t('admin.servers.create')}</button>
        </div>
      </form>
    </Modal>
  );
}
