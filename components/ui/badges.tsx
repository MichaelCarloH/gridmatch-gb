import { titleCase } from '@/lib/format';

export function DataOriginBadge({ origin }: { origin: string }) {
  return <span className={`badge origin-${origin}`}>{titleCase(origin)}</span>;
}

export const OriginBadge = DataOriginBadge;

export function StatusBadge({ status }: { status: string }) {
  return <span className={`badge status-${status}`}>{titleCase(status)}</span>;
}

export function ScenarioBadge({
  children = 'Scenario'
}: {
  children?: React.ReactNode;
}) {
  return <span className="badge scenario-badge">{children}</span>;
}
