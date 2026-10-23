import { useTranslation } from 'react-i18next';
import type { ServerIssue } from '../../lib/dtc/errorDetails';
import type { Issue } from '../../lib/dtc/validate';

interface Props {
  issues: Issue[];
  serverIssues: ServerIssue[];
}

/** Live checks (errors block the download, warnings do not) and the exact messages of a rejected generation. */
export function IssuesPanel({ issues, serverIssues }: Props) {
  const { t } = useTranslation();
  const errors = issues.filter((i) => i.severity === 'error');
  const warnings = issues.filter((i) => i.severity === 'warning');
  const text = (i: Issue) => t(`dtc.issues.${i.key}`, i.params);
  return (
    <>
      {serverIssues.length > 0 && (
        <div className="notice notice-error" role="alert">
          <b>{t('dtc.server.rejected')}</b>
          <ul>{serverIssues.map((i) => <li key={i.message}>{i.message}</li>)}</ul>
        </div>
      )}
      {errors.length > 0 && (
        <div className="notice notice-error" role="alert">
          <b>{t('dtc.issues.fix')}</b>
          <ul>{errors.map((i) => <li key={`${i.key}-${i.pointId ?? ''}-${i.params?.n ?? ''}`}>{text(i)}</li>)}</ul>
        </div>
      )}
      {warnings.length > 0 && (
        <div className="notice notice-warn" role="note">
          <ul>{warnings.map((i) => <li key={i.key}>{text(i)}</li>)}</ul>
        </div>
      )}
    </>
  );
}
