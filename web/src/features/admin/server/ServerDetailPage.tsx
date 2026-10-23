import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PageHeader } from '../../../components/Card';
import { ErrorState } from '../../../components/states/ErrorState';
import { Loading } from '../../../components/states/Loading';
import { OnlineBadge } from '../OnlineBadge';
import { ConnectSection } from './ConnectSection';
import { DangerSection } from './DangerSection';
import { DcsBotSection } from './DcsBotSection';
import { DirtyProvider } from './dirty';
import { FootholdSection } from './FootholdSection';
import { GeneralSection } from './GeneralSection';
import { MissionsSection } from './MissionsSection';
import { StatusSection } from './StatusSection';
import { TacviewSection } from './TacviewSection';
import { UnsavedGuard } from './UnsavedGuard';
import { useServerDetail } from './useServerDetail';

const SECTIONS = ['connect', 'status', 'general', 'foothold', 'tacview', 'missions', 'dcsbot', 'danger'] as const;
const SECTION_TITLES: Record<(typeof SECTIONS)[number], string> = {
  status: 'admin.server.status.title',
  general: 'admin.server.general.title',
  connect: 'admin.server.connect.title',
  foothold: 'admin.server.foothold.title',
  tacview: 'admin.server.tacview.title',
  missions: 'admin.server.missions.title',
  dcsbot: 'admin.server.dcsbot.title',
  danger: 'admin.server.danger.title',
};

export default function ServerDetailPage() {
  const { t } = useTranslation();
  const { id = '' } = useParams();
  const { data: server, error, reload, apply } = useServerDetail(id);

  if (!server) {
    return error ? (
      <>
        <Link to="/admin">&larr; {t('admin.server.back')}</Link>
        <ErrorState error={error} onRetry={reload} />
      </>
    ) : (
      <Loading />
    );
  }

  const props = { server, apply };
  return (
    <DirtyProvider>
      {(dirtyCount) => (
        <>
          <UnsavedGuard active={dirtyCount > 0} />
          <Link to="/admin">&larr; {t('admin.server.back')}</Link>
          <PageHeader title={server.name}>
            <OnlineBadge online={server.online} />
          </PageHeader>
          <nav className="section-nav" aria-label={server.name}>
            {SECTIONS.map((s) => (
              <a key={s} href={`#sec-${s}`}>{t(SECTION_TITLES[s])}</a>
            ))}
          </nav>
          <div className="server-sections">
            <section id="sec-connect"><ConnectSection server={server} apply={apply} onChanged={reload} /></section>
            <section id="sec-status"><StatusSection server={server} /></section>
            <section id="sec-general"><GeneralSection {...props} /></section>
            <section id="sec-foothold"><FootholdSection {...props} /></section>
            <section id="sec-tacview"><TacviewSection {...props} /></section>
            <section id="sec-missions"><MissionsSection {...props} /></section>
            <section id="sec-dcsbot"><DcsBotSection {...props} /></section>
            <section id="sec-danger"><DangerSection server={server} /></section>
          </div>
        </>
      )}
    </DirtyProvider>
  );
}
