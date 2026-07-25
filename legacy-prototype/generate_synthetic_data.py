"""Generate deterministic half-hourly demonstration data; no credentials required."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv, math, random

random.seed(42)
output = Path(__file__).parents[1] / 'data' / 'synthetic_half_hourly.csv'
output.parent.mkdir(exist_ok=True)
start = datetime(2026, 7, 24, tzinfo=timezone.utc)
sites = [('Mercia Foods', 'demand', 1.25), ('Northline Logistics', 'demand', .72), ('East Fen Solar', 'solar', 1.8), ('Moorland Wind', 'wind', 2.2), ('West Coast Wind', 'wind', 1.6)]

with output.open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=['timestamp_utc', 'settlement_period', 'site', 'kind', 'mwh'])
    writer.writeheader()
    for period in range(48):
        hour = period / 2
        for site, kind, capacity in sites:
            if kind == 'demand':
                profile = .48 + .28 * math.sin((hour - 7) * math.pi / 12) ** 2 + (.12 if 7 < hour < 18 else 0)
            elif kind == 'solar':
                profile = max(0, math.sin((hour - 4.5) * math.pi / 15)) * .72
            else:
                profile = .38 + .22 * math.sin((hour + (0 if site.startswith('Moor') else 3)) * math.pi / 12) ** 2
            value = max(0, capacity * profile * .5 * (1 + random.uniform(-.08, .08)))
            writer.writerow({'timestamp_utc': (start + timedelta(minutes=30 * period)).isoformat(), 'settlement_period': period + 1, 'site': site, 'kind': kind, 'mwh': round(value, 3)})

print(f'Wrote {output}')
