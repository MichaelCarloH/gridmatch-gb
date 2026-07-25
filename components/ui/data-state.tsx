import { EmptyState, ErrorState, LoadingSkeleton } from './states';

export function DataState({
  loading,
  error,
  empty,
  onRetry
}: {
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  onRetry?: () => void;
}) {
  if (loading) {
    return <LoadingSkeleton />;
  }
  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }
  if (empty) return <EmptyState />;
  return null;
}
