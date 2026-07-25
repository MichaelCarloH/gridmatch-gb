import { titleCase } from '@/lib/format';

export function OriginBadge({ origin }: { origin: string }) {
  return <span className={`badge origin-${origin}`}>{titleCase(origin)}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  return <span className={`badge status-${status}`}>{titleCase(status)}</span>;
}
