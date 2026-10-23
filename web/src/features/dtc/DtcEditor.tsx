import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { DtcAircraft, DtcTerrain } from '../../api/types.dtc';
import { Card } from '../../components/Card';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { allLists } from '../../lib/dtc/lists';
import { radiosEdited } from '../../lib/dtc/radioBaseline';
import { radioInputIssues } from '../../lib/dtc/radioValidate';
import { blockingIssues, validateDraft } from '../../lib/dtc/validate';
import { errorKey } from '../../lib/errors';
import { DownloadBar } from './DownloadBar';
import { DtcMap } from './DtcMap';
import { ElevationFooter } from './ElevationFooter';
import { ImportBox } from './ImportBox';
import { IssuesPanel } from './IssuesPanel';
import { ListSelector } from './ListSelector';
import { ListSettings } from './ListSettings';
import { PointList } from './PointList';
import { PreservedBox } from './PreservedBox';
import { RadiosCard } from './radios/RadiosCard';
import { useInvalidInputs } from './radios/useInvalidInputs';
import { useRadioActions } from './radios/useRadioActions';
import { useRadioDefaults } from './radios/useRadioDefaults';
import { AircraftStep, NameStep, TerrainStep } from './SetupSteps';
import { useDtcActions } from './useDtcActions';
import { useDtcDownload } from './useDtcDownload';
import { useDtcDraft } from './useDtcDraft';
import { useDtcImport } from './useDtcImport';
import { useDtcStart } from './useDtcStart';
import { useElevationFill, type Fill } from './useElevationFill';

type Confirm = { kind: 'aircraft'; id: string } | { kind: 'clear' } | null;

interface Props {
  aircraft: DtcAircraft[];
  terrains: DtcTerrain[];
}

export function DtcEditor({ aircraft, terrains }: Props) {
  const { t } = useTranslation();
  const store = useDtcDraft();
  const { draft } = store;
  const [confirm, setConfirm] = useState<Confirm>(null);
  const applyFills = useRef<(f: Fill[]) => void>(() => undefined);
  const elevation = useElevationFill(store.getModel, (f) => applyFills.current(f));
  const actions = useDtcActions({ draft, update: store.update, editModel: store.editModel, queueElevation: elevation.queue });
  applyFills.current = actions.applyFills;
  const importer = useDtcImport(store.load);
  const download = useDtcDownload(draft, store.dropTemplate);
  const starter = useDtcStart(draft?.model.terrain ?? null, store.begin);
  const radioActions = useRadioActions(store.editModel, draft?.radiosBase);
  const invalidRadio = useInvalidInputs();

  const info = aircraft.find((a) => a.id === draft?.model.aircraft);
  const radioDefaults = useRadioDefaults(draft, !!info?.supports.includes('radios'), store.update);
  const issues = draft ? [...validateDraft(draft.model, info), ...radioInputIssues(invalidRadio.count)] : [];
  const hasWork = !!draft && (allLists(draft.model).some((l) => l.points.length > 0) || radiosEdited(draft.model, draft.radiosBase));

  const pickAircraft = (id: string) => (hasWork ? setConfirm({ kind: 'aircraft', id }) : void starter.start(id));
  const accept = () => {
    if (confirm?.kind === 'aircraft') void starter.start(confirm.id);
    if (confirm?.kind === 'clear') { store.clear(); importer.clear(); }
    setConfirm(null);
  };

  return (
    <>
      <Card title={t('dtc.steps.title')}>
        <div className="dtc-steps">
          <AircraftStep aircraft={aircraft} value={draft?.model.aircraft ?? ''} onChange={pickAircraft} />
          <TerrainStep terrains={terrains} model={draft?.model ?? null} onChange={actions.setTerrain} />
          <ImportBox importer={importer} fileName={draft?.fileName ?? null} />
          <NameStep model={draft?.model ?? null} onChange={actions.setName} />
        </div>
        {starter.busy && <p className="muted" role="status">{t('dtc.steps.starting')}</p>}
        {starter.error && <div className="notice notice-error" role="alert">{t(`errors.${errorKey(starter.error)}`)}</div>}
      </Card>
      <div className="dtc-layout">
        <Card className="dtc-map-card">
          <DtcMap
            model={draft?.model ?? null} active={draft?.active} approx={draft?.approx ?? {}} revision={store.revision}
            handlers={{ onAdd: actions.addAt, onDrag: actions.dragTo, onRemove: actions.remove, onActivate: actions.setActive }}
            onAddPlace={actions.addPlace}
          />
          <p className="muted small">{t('dtc.map.help')}</p>
        </Card>
        <Card title={t('dtc.points.title')}>
          {draft ? (
            <>
              <ListSelector model={draft.model} active={draft.active} onSelect={actions.setActive} />
              <ListSettings model={draft.model} active={draft.active} actions={actions} />
              <PointList model={draft.model} list={draft.active} approx={draft.approx} serverIssues={download.issues} actions={actions} />
              {info && <PreservedBox aircraft={info} warnings={importer.warnings} />}
            </>
          ) : <p className="muted">{t('dtc.points.pickFirst')}</p>}
        </Card>
      </div>
      {draft && (
        <RadiosCard
          info={info} defaults={radioDefaults} model={draft.model} base={draft.radiosBase} fromFile={draft.templateId !== null} act={radioActions} report={invalidRadio.report}
        />
      )}
      {draft && (
        <Card>
          <IssuesPanel issues={issues} serverIssues={download.issues} />
          <DownloadBar blocking={blockingIssues(issues)} download={download} onClear={() => setConfirm({ kind: 'clear' })} />
        </Card>
      )}
      <ElevationFooter state={elevation.state} />
      <ConfirmDialog
        open={confirm !== null} title={t(confirm?.kind === 'clear' ? 'dtc.draft.clear' : 'dtc.steps.switchTitle')}
        message={t(confirm?.kind === 'clear' ? 'dtc.draft.clearAsk' : 'dtc.steps.switchAsk')} onConfirm={accept} onCancel={() => setConfirm(null)}
      />
    </>
  );
}
