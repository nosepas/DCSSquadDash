import { useMemo } from 'react';
import type { DtcModel } from '../../../api/types.dtc';
import type { DtcRadios, InitialRadioId, PresetRadioId, RadioInitial, RadioSettings } from '../../../api/types.radios';
import { resetInitial, resetPreset, resetRadio } from '../../../lib/dtc/radioBaseline';
import { setChannelFrequency, setGuardReceiver, setInitialHf, setInitialRadio, setPresetRadio, setPresetText } from '../../../lib/dtc/radioEdit';

type Edit = (fn: (m: DtcModel) => DtcModel) => void;

/** Every radio edit of the draft (all immutable helpers from lib/dtc/radioEdit and radioBaseline). */
export function useRadioActions(editModel: Edit, base: DtcRadios | undefined) {
  return useMemo(() => ({
    channel: (radio: string, ch: number, mhz: number) => editModel((m) => setChannelFrequency(m, radio, ch, mhz)),
    presetText: (i: number, key: 'call_sign' | 'unit_id', v: string) => editModel((m) => setPresetText(m, i, key, v)),
    presetRadio: (i: number, id: PresetRadioId, p: Partial<RadioSettings>) => editModel((m) => setPresetRadio(m, i, id, p)),
    initialRadio: (id: InitialRadioId, p: Partial<RadioInitial>) => editModel((m) => setInitialRadio(m, id, p)),
    initialHf: (p: Parameters<typeof setInitialHf>[1]) => editModel((m) => setInitialHf(m, p)),
    guard: (on: boolean) => editModel((m) => setGuardReceiver(m, on)),
    resetRadio: (id: string) => editModel((m) => resetRadio(m, base, id)),
    resetPreset: (i: number) => editModel((m) => resetPreset(m, base, i)),
    resetInitial: () => editModel((m) => resetInitial(m, base)),
  }), [editModel, base]);
}

export type RadioActions = ReturnType<typeof useRadioActions>;
