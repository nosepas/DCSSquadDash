import { useTranslation } from 'react-i18next';
import { fetchDtcAircraft, fetchDtcTerrains } from '../../api/dtc';
import { PageHeader } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { DtcEditor } from './DtcEditor';

export default function DtcPage() {
  const { t } = useTranslation();
  const aircraft = useAsync((signal) => fetchDtcAircraft(signal), []);
  const terrains = useAsync((signal) => fetchDtcTerrains(signal), []);
  return (
    <>
      <PageHeader title={t('dtc.title')} />
      <p className="muted">{t('dtc.intro')}</p>
      <AsyncView state={aircraft}>
        {(a) => <AsyncView state={terrains}>{(tr) => <DtcEditor aircraft={a} terrains={tr} />}</AsyncView>}
      </AsyncView>
    </>
  );
}
