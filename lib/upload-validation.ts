import type { Dictionary } from './types';

const REQUIRED = ['timestamp', 'consumption_kwh'] as const;

function splitCsvLine(line: string): string[] {
  return line.split(',').map((value) => value.trim().replace(/^"|"$/g, ''));
}

export function validateMeterCsv(text: string) {
  const lines = text.replace(/^\uFEFF/, '').split(/\r?\n/).filter(Boolean);
  const headers = splitCsvLine(lines[0] ?? '').map((value) => value.toLowerCase());
  const missingColumns = REQUIRED.filter((name) => !headers.includes(name));
  if (missingColumns.length) {
    return {
      readiness: 'rejected',
      quality_score: 0,
      received_rows: Math.max(lines.length - 1, 0),
      expected_rows: 0,
      completeness: 0,
      duplicates: 0,
      anomalies: 0,
      inferred_frequency_minutes: null,
      dst_issues: 'requires Phase 4 API',
      recommended_actions: [`Add required columns: ${missingColumns.join(', ')}`],
      annotated_preview: [] as Dictionary[],
      permanent_storage: false,
      validation_mode: 'browser schema mirror'
    };
  }
  const timestampIndex = headers.indexOf('timestamp');
  const valueIndex = headers.indexOf('consumption_kwh');
  const seen = new Set<string>();
  let duplicates = 0;
  let anomalies = 0;
  const preview: Dictionary[] = [];
  const timestamps: number[] = [];
  for (const line of lines.slice(1)) {
    const cells = splitCsvLine(line);
    const timestamp = cells[timestampIndex];
    const value = Number(cells[valueIndex]);
    const parsed = Date.parse(timestamp);
    const flags: string[] = [];
    if (!Number.isFinite(parsed)) flags.push('invalid_timestamp');
    if (!Number.isFinite(value) || value < 0) flags.push('invalid_consumption');
    if (seen.has(timestamp)) {
      flags.push('duplicate');
      duplicates += 1;
    }
    seen.add(timestamp);
    if (Number.isFinite(parsed)) timestamps.push(parsed);
    if (flags.length) anomalies += 1;
    if (preview.length < 10) {
      preview.push({
        timestamp,
        consumption_kwh: cells[valueIndex],
        quality_flag: flags.join('|') || 'valid'
      });
    }
  }
  timestamps.sort((a, b) => a - b);
  const intervals = timestamps.slice(1).map((value, index) => (value - timestamps[index]) / 60000).filter((value) => value > 0);
  const frequency = intervals.length
    ? intervals.sort((a, b) => a - b)[Math.floor(intervals.length / 2)]
    : null;
  const expected = timestamps.length > 1 && frequency
    ? Math.round((timestamps[timestamps.length - 1] - timestamps[0]) / (frequency * 60000)) + 1
    : timestamps.length;
  const completeness = expected ? Math.min(seen.size / expected, 1) : 0;
  const frequencyPenalty = frequency === 30 ? 0 : 15;
  const score = Math.max(0, Math.min(100, 100 * completeness - 50 * anomalies / Math.max(lines.length - 1, 1) - frequencyPenalty));
  const ready = frequency === 30 && completeness >= 0.98 && anomalies === 0;
  return {
    readiness: ready ? 'ready' : 'manual_review',
    quality_score: Number(score.toFixed(2)),
    received_rows: Math.max(lines.length - 1, 0),
    expected_rows: expected,
    completeness,
    duplicates,
    anomalies,
    inferred_frequency_minutes: frequency,
    dst_issues: 'requires Phase 4 API',
    recommended_actions: ready
      ? ['Dataset is ready for in-memory demo use.']
      : ['Review flagged rows and confirm half-hourly Europe/London settlement coverage.'],
    annotated_preview: preview,
    permanent_storage: false,
    validation_mode: 'browser schema mirror'
  };
}
