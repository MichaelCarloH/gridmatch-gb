import { Icon } from './icon';
import { HowCalculatedDrawer } from './how-calculated-drawer';

export function MetricCard({
  label,
  value,
  detail,
  tone = 'ink',
  icon = 'chart',
  origin = 'simulated',
  explanation
}: {
  label: string;
  value: string;
  detail: string;
  tone?: 'ink' | 'green' | 'blue' | 'amber';
  icon?: string;
  origin?: 'public' | 'simulated' | 'uploaded';
  explanation?: {
    source: string;
    calculation: string;
    limitation?: string;
  };
}) {
  return (
    <article className={`metric-card ${tone}`}>
      <div className="metric-label"><span className="metric-icon"><Icon name={icon} /></span>{label}</div>
      <strong>{value}</strong>
      <p>{detail}</p>
      <span className={`badge origin-${origin}`}>{origin}</span>
      {explanation && <HowCalculatedDrawer {...explanation} />}
    </article>
  );
}
