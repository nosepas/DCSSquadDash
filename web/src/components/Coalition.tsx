import { useTranslation } from 'react-i18next';
import type { Coalition } from '../api/types';
import { percent } from '../lib/format';

/** Coalition label with a colour dot and text, so colour is never the only cue. */
export function CoalitionBadge({ coalition }: { coalition: Coalition | null }) {
  const { t } = useTranslation();
  if (!coalition) return <span className="muted">–</span>;
  return (
    <span className={`badge badge-${coalition}`}>
      <span className="dot" aria-hidden="true" />
      {t(`coalition.${coalition}`)}
    </span>
  );
}

/** Red vs blue (vs neutral) proportion bar. */
export function CoalitionBar({ counts }: { counts: Record<Coalition, number> }) {
  const { t } = useTranslation();
  const total = counts.red + counts.blue + counts.neutral;
  const label = (['red', 'blue', 'neutral'] as const).map((c) => `${t(`coalition.${c}`)} ${counts[c]}`).join(', ');
  return (
    <div className="cbar" role="img" aria-label={label}>
      {(['red', 'blue', 'neutral'] as const).map((c) => (
        <span key={c} className={`cbar-seg cbar-${c}`} style={{ width: `${percent(counts[c], total)}%` }} />
      ))}
    </div>
  );
}
