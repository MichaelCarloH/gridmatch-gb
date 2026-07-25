'use client';

export function Bars({
  rows,
  labelKey,
  valueKey,
  unit,
  color = 'var(--green)'
}: {
  rows: Record<string, any>[];
  labelKey: string;
  valueKey: string;
  unit: string;
  color?: string;
}) {
  const max = Math.max(...rows.map((row) => Math.abs(Number(row[valueKey]))), 1);
  return (
    <div className="bars" aria-label={`${valueKey} in ${unit}`}>
      {rows.map((row, index) => (
        <div className="bar-row" key={`${row[labelKey]}-${index}`}>
          <span>{String(row[labelKey]).replaceAll('_', ' ')}</span>
          <div><i style={{ width: `${Math.abs(Number(row[valueKey])) / max * 100}%`, background: color }} /></div>
          <b>{Number(row[valueKey]).toFixed(2)} {unit}</b>
        </div>
      ))}
    </div>
  );
}
