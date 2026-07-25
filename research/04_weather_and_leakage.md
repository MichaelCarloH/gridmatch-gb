# Weather availability and leakage

## Verified public facts

Weather `issue_time` identifies when information was available; `valid_time` identifies when the weather applies. A realised historical observation is not equivalent to a historical forecast vintage. Using realised future weather for a day-ahead decision creates leakage.

## Observed data findings

The cached public Open-Meteo artifact contains 48 hourly ERA5 records at one London coordinate and has no missing values in the requested temperature, cloud, shortwave-radiation, 10 m wind, direction, and surface-pressure fields. The 12 site coordinates used for alignment examples are simulated and their distance from the weather point is retained.

## Modelling assumptions

Demand examples use temperature and cloud; solar examples use shortwave radiation, cloud, and temperature; wind examples use 10 m wind speed, direction, and pressure. These are availability demonstrations only. No feature engineering or forecast model is implemented.

## Prototype limitations

ERA5 is historical realised weather, not a complete operational forecast-vintage archive. One London grid point cannot represent all simulated site conditions, and 10 m wind is not a substitute for hub-height wind.

## Production recommendations

Archive forecast vintages at issue time, enrich every site coordinate, retain provider/model/run identifiers, and enforce `issue_time <= decision_time < valid_time` in training and validation. Missing-weather fallbacks must be explicit and must never backfill from future observations.
