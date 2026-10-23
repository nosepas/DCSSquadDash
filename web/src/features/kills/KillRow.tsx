import { useTranslation } from 'react-i18next';
import type { Coalition, KillEvent } from '../../api/types';
import { formatTime } from '../../lib/format';

interface PartyProps {
  name: string | null;
  unit: string | null;
  coalition: Coalition | null;
  isPlayer: boolean;
}

function Party({ name, unit, coalition, isPlayer }: PartyProps) {
  const { t } = useTranslation();
  return (
    <span className={`party party-${coalition ?? 'neutral'}`}>
      <span className="dot" aria-hidden="true" />
      <span className="mono">{name ?? t('kills.unknownActor')}</span>
      {unit && <span className="muted small mono"> {unit}</span>}
      {!isPlayer && <span className="tag">{t('kills.ai')}</span>}
    </span>
  );
}

/** One engagement line: used in the kill log table and in the dashboard feed. */
export function KillSummary({ kill }: { kill: KillEvent }) {
  const { t } = useTranslation();
  const unknown = t('kills.unknownActor');
  return (
    <span className="kill-line">
      <Party name={kill.actor_name} unit={kill.actor_unit} coalition={kill.actor_coalition} isPlayer />
      <span className="kill-arrow" aria-hidden="true">
        {'➜'}
      </span>
      <span className="sr-only">
        {t('kills.killed', { killer: kill.actor_name ?? unknown, victim: kill.target_name ?? unknown })}
      </span>
      <Party name={kill.target_name} unit={kill.target_unit} coalition={kill.target_coalition} isPlayer={kill.target_is_player} />
    </span>
  );
}

export function KillTime({ iso }: { iso: string }) {
  const { i18n } = useTranslation();
  return (
    <time dateTime={iso} className="mono muted">
      {formatTime(iso, i18n.language)}
    </time>
  );
}
