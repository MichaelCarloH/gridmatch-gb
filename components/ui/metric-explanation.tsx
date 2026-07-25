export function MetricExplanation({
  source,
  calculation,
  limitation
}: {
  source: string;
  calculation: string;
  limitation?: string;
}) {
  return (
    <div className="metric-explanation">
      <div><span>Source</span><b>{source}</b></div>
      <div><span>Calculation</span><b>{calculation}</b></div>
      {limitation && <div><span>Boundary</span><b>{limitation}</b></div>}
    </div>
  );
}
