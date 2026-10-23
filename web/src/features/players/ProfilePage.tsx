import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { fetchProfile } from '../../api/players';
import { PageHeader } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { ProfileView } from './ProfileView';

export function ProfileLoader({ ucid }: { ucid: string }) {
  const state = useAsync((signal) => fetchProfile(ucid, signal), [ucid]);
  return <AsyncView state={state}>{(p) => <ProfileView profile={p} />}</AsyncView>;
}

export default function ProfilePage() {
  const { t } = useTranslation();
  const { ucid = '' } = useParams();
  return (
    <>
      <PageHeader title={t('profile.title')} />
      <ProfileLoader ucid={ucid} />
    </>
  );
}
