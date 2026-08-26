# Data and ML plan

## Source registry

`GET /data/sources` exposes the MVP source register, including use, fields, coverage, frequency, license context and limitations.

| Source | MVP role | Production connection |
| --- | --- | --- |
| [data.gov.in mandi prices](https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi) | Price schema and seeded sample records | Scheduled API ingestion with retained raw payloads |
| [Agmarknet](https://agmarknet.gov.in/) | Historical price/arrival research source | Authorized historical extraction and validation pipeline |
| [Open-Meteo historical weather](https://open-meteo.com/en/docs/historical-weather-api) | Weather feature source plan | Daily coordinate joins for precipitation, temperature and soil moisture |
| [Copernicus Data Space](https://dataspace.copernicus.eu/) | Remote-sensing/vegetation index source plan | Parcel or block-level satellite feature pipeline |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | Mapping and road-network source plan | Provider-compliant OSRM, OpenRouteService, or managed routing matrix |

## Baseline models in this prototype

- Price: deterministic baseline from current modal price, grade adjustment, availability horizon, and arrival-pressure proxy.
- Demand: regional activity baseline with a labeled confidence and forecast horizon.
- Quality: tomato-only AI-assisted placeholder that preserves declared grade and requires inspection evidence before payment release.
- Matching: weighted, explainable policy score instead of an opaque model.

These endpoints create transparent demonstration outputs, not production ML claims. The API labels them as baseline or AI-assisted demo output.

## Production training design

1. Version raw mandi, arrival, weather, road and transaction snapshots with source timestamps and classification.
2. Build features for commodity, variety, market, lagged prices, arrivals, weather, crop calendar, route distance, shelf-life and transaction behavior.
3. Train a price baseline (seasonal naive / gradient boosting) before evaluating spatial-temporal or graph methods; use date-based holdout splits.
4. Track MAE, MAPE/sMAPE, calibration, commodity-market slices, missing-data rate, latency, drift, and farmer-realization outcomes.
5. Human review any price alert, payment decision, quality dispute, or recommendation that impacts a participant's money or access.

## Fairness and privacy

Do not use caste, religion, gender, or other sensitive personal attributes for ranking. Keep exact farm coordinates restricted to participants who need them for logistics. Obtain permission before using transaction history or farm data for model training. Show an explanation and a dispute path for material recommendations.
