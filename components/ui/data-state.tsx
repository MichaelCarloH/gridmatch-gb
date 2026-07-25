import { Icon } from './icon';

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
    return <div className="state-card"><span className="spinner" />Loading artifact data…</div>;
  }
  if (error) {
    return (
      <div className="state-card error-state">
        <Icon name="alert" />
        <div><strong>Data could not be loaded</strong><p>{error}</p></div>
        {onRetry && <button className="button ghost" onClick={onRetry}>Retry</button>}
      </div>
    );
  }
  if (empty) return <div className="state-card">No records match these filters.</div>;
  return null;
}
