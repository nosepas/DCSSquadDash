import type { ReactNode } from 'react';
import type { AsyncState } from '../../hooks/useAsync';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';
import { Loading } from './Loading';

interface Props<T> {
  state: AsyncState<T>;
  children: (data: T) => ReactNode;
  /** Return true when the data should render the empty state. */
  isEmpty?: (data: T) => boolean;
  emptyMessage?: string;
}

/** Shared loading / error / empty handling. Keeps showing stale data while a refetch is in flight. */
export function AsyncView<T>({ state, children, isEmpty, emptyMessage }: Props<T>) {
  if (state.data === undefined) {
    if (state.error) return <ErrorState error={state.error} onRetry={state.reload} />;
    return <Loading />;
  }
  if (isEmpty?.(state.data)) return <EmptyState message={emptyMessage} />;
  return <>{children(state.data)}</>;
}
