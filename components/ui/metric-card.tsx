import { Icon } from './icon';

export function MetricCard({
  label,
  value,
  detail,
  tone = 'ink',
  icon = 'chart'
}: {
  label: string;
  value: string;
  detail: string;
  tone?: 'ink' | 'green' | 'blue' | 'amber';
  icon?: string;
}) {
  return (
    <article className={`metric-card ${tone}`}>
      <div className="metric-label"><span className="metric-icon"><Icon name={icon} /></span>{label}</div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}
