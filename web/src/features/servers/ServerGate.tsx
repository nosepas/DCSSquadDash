import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { ServerSummary } from '../../api/types';
import { EmptyState } from '../../components/states/EmptyState';
import { ErrorState } from '../../components/states/ErrorState';
import { Loading } from '../../components/states/Loading';
import { useServers } from './ServerContext';

interface Props {
  /** Pages that only make sense for Foothold missions redirect generic servers to the map. */
  footholdOnly?: boolean;
  children: (server: ServerSummary) => ReactNode;
}

/** Resolves the selected server (loading / error / none) before rendering a server-scoped page. */
export function ServerGate({ footholdOnly, children }: Props) {
  const { t } = useTranslation();
  const { list, current } = useServers();
  if (!current) {
    if (list.loading) return <Loading />;
    if (list.error) return <ErrorState error={list.error} onRetry={list.reload} />;
    return <EmptyState message={t('header.noServers')} />;
  }
  if (footholdOnly && current.mission_type !== 'foothold') return <Navigate to="/map" replace />;
  return <>{children(current)}</>;
}
