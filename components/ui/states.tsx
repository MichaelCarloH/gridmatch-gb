'use client';

import { Icon } from './icon';

export function LoadingSkeleton({
  label = 'Loading artifact data'
}: {
  label?: string;
}) {
  return (
    <div className="state-card loading-skeleton" role="status" aria-live="polite">
      <span className="spinner" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({
  message,
  onRetry
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="state-card error-state" role="alert">
      <Icon name="alert" />
      <div>
        <strong>Data could not be loaded</strong>
        <p>{message}</p>
      </div>
      {onRetry && (
        <button className="button ghost" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  message = 'No records match these filters.'
}: {
  message?: string;
}) {
  return (
    <div className="state-card empty-state" role="status">
      <Icon name="inbox" />
      <span>{message}</span>
    </div>
  );
}
