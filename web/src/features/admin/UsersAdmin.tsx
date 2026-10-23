import { useTranslation } from 'react-i18next';
import { listUsers, setUserRole } from '../../api/admin';
import type { AdminUser, Role } from '../../api/types';
import { Card } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { ErrorState } from '../../components/states/ErrorState';
import { useAction } from '../../hooks/useAction';
import { useAsync } from '../../hooks/useAsync';
import { formatDateTime } from '../../lib/format';
import { useAuth } from '../auth/AuthContext';

export default function UsersAdmin() {
  const { t, i18n } = useTranslation();
  const users = useAsync(listUsers, []);
  const { user: me } = useAuth();
  const action = useAction();

  const change = async (u: AdminUser, role: Role) => {
    if (await action.run(() => setUserRole(u.user_id, role))) users.reload();
  };

  return (
    <Card>
      {action.error && <ErrorState error={action.error} />}
      <AsyncView state={users} isEmpty={(d) => d.length === 0} emptyMessage={t('admin.users.empty')}>
        {(list) => (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">{t('admin.users.user')}</th>
                  <th scope="col">{t('admin.users.role')}</th>
                  <th scope="col">{t('admin.users.lastLogin')}</th>
                </tr>
              </thead>
              <tbody>
                {list.map((u) => (
                  <tr key={u.user_id}>
                    <th scope="row" className="mono">{u.discord_name ?? `#${u.user_id}`}</th>
                    <td>
                      <select
                        aria-label={t('admin.users.changeRole', { name: u.discord_name ?? u.user_id })}
                        value={u.role}
                        disabled={action.busy || u.user_id === me?.user_id}
                        onChange={(e) => void change(u, e.target.value as Role)}
                      >
                        <option value="user">{t('auth.role.user')}</option>
                        <option value="admin">{t('auth.role.admin')}</option>
                      </select>
                    </td>
                    <td className="mono">{formatDateTime(u.last_login_at, i18n.language)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </AsyncView>
    </Card>
  );
}
