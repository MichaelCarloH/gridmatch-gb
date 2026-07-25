'use client';

type Series = { key: string; label: string; color: string };

export function LineChart({
  rows,
  series,
  unit,
  height = 280
}: {
  rows: Record<string, any>[];
  series: Series[];
  unit: string;
  height?: number;
}) {
  const width = 900;
  const pad = { x: 44, y: 26 };
  const values = rows.flatMap((row) =>
    series.map((item) => Number(row[item.key])).filter(Number.isFinite)
  );
  if (!rows.length || !values.length) return <div className="chart-empty">No chart data</div>;
  const min = Math.min(0, ...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const x = (index: number) => pad.x + (index / Math.max(rows.length - 1, 1)) * (width - pad.x * 2);
  const y = (value: number) => height - pad.y - ((value - min) / range) * (height - pad.y * 2);
  return (
    <div className="chart-wrap">
      <div className="chart-legend">
        {series.map((item) => <span key={item.key}><i style={{ background: item.color }} />{item.label}</span>)}
        <b>{unit}</b>
      </div>
      <svg className="line-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${series.map((s) => s.label).join(', ')} in ${unit}`}>
        {[0, .25, .5, .75, 1].map((tick) => {
          const value = min + range * tick;
          return <g key={tick}><line x1={pad.x} x2={width - pad.x} y1={y(value)} y2={y(value)} className="grid-line" /><text x={pad.x - 8} y={y(value) + 4}>{value.toFixed(1)}</text></g>;
        })}
        <line x1={pad.x} x2={width - pad.x} y1={y(0)} y2={y(0)} className="zero-line" />
        {series.map((item) => (
          <polyline
            key={item.key}
            points={rows.map((row, index) => `${x(index)},${y(Number(row[item.key]))}`).join(' ')}
            fill="none"
            stroke={item.color}
            strokeWidth="3"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
    </div>
  );
}
