export const number = (
  value: number | null | undefined,
  digits = 1
): string =>
  value == null || !Number.isFinite(value)
    ? '—'
    : new Intl.NumberFormat('en-GB', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
      }).format(value);

export const compact = (value: number | null | undefined): string =>
  value == null || !Number.isFinite(value)
    ? '—'
    : new Intl.NumberFormat('en-GB', {
        notation: 'compact',
        maximumFractionDigits: 1
      }).format(value);

export const percent = (
  value: number | null | undefined,
  digits = 0
): string => (value == null ? '—' : `${number(value * 100, digits)}%`);

export const gbp = (value: number | null | undefined): string =>
  value == null
    ? '—'
    : new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: 'GBP',
        maximumFractionDigits: 0
      }).format(value);

export const timestamp = (value: string | null | undefined): string =>
  value
    ? new Intl.DateTimeFormat('en-GB', {
        timeZone: 'Europe/London',
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
      }).format(new Date(value))
    : '—';

export const titleCase = (value: string): string =>
  value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
