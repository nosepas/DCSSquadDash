import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getAgentPackageInfo, requestAgentPackage } from '../../../../api/agentPackage';
import { useAction } from '../../../../hooks/useAction';
import { useAsync } from '../../../../hooks/useAsync';
import { saveBlob } from '../../../../lib/download';
import { readStored, writeStored } from '../../../../lib/storage';

export interface DownloadMemory {
  at: number;
  minutes: number;
  filename: string;
}

const key = (serverId: string) => `fox3.agentDownload.${serverId}`;

function load(serverId: string): DownloadMemory | null {
  try {
    const m = JSON.parse(readStored(key(serverId)) ?? 'null') as Partial<DownloadMemory> | null;
    return m && typeof m.at === 'number' && typeof m.minutes === 'number'
      ? { at: m.at, minutes: m.minutes, filename: String(m.filename ?? '') }
      : null;
  } catch {
    return null;
  }
}

/** Installer availability, the download action and a per-server memory of the last download (survives reloads). */
export function useAgentPackage(serverId: string) {
  const { i18n } = useTranslation();
  const info = useAsync((signal) => getAgentPackageInfo(signal), []);
  const { run, busy, error } = useAction();
  const [memory, setMemory] = useState<DownloadMemory | null>(() => load(serverId));

  const download = useCallback(async () => {
    await run(async () => {
      const file = await requestAgentPackage(serverId, i18n.language);
      const next = { at: Date.now(), minutes: file.expiresMinutes, filename: file.filename };
      writeStored(key(serverId), JSON.stringify(next));
      setMemory(next);
      saveBlob(file);
    });
  }, [run, serverId, i18n.language]);

  return { info: info.data, infoLoading: info.loading, reloadInfo: info.reload, memory, download, busy, error };
}

export type AgentPackage = ReturnType<typeof useAgentPackage>;
