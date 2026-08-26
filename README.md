# AgriPlace

AgriPlace is a farmer-first marketplace prototype for the SIH problem: direct farmer-to-buyer trade with transparent price intelligence, pooled logistics, protected-payment workflow, and role-based operations.

The app seeds a complete 2,000 kg tomato scenario from Nashik to Mumbai:

- Ramesh Farm (1,000 kg), Kavita Farm (600 kg), and Sahyadri FPO (400 kg)
- Mumbai FreshMart buyer requirement and protected payment hold
- transporter trip, OR-Tools capacity-aware route, pickup evidence, delivery confirmation, audit log

## Run locally

Create the Python environment and install backend dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

Start the API in one terminal:

```bash
.venv/bin/uvicorn backend.app.main:app --reload --port 8000
```

Serve the dependency-free responsive frontend in another terminal:

```bash
python3 -m http.server 3000 --directory frontend
```

Open `http://127.0.0.1:3000`. The page signs into the selected demo workspace automatically. Demo password: `AgriPlace@123`.

## Verification

```bash
.venv/bin/pytest -q
node --check frontend/app.js
```

## What is real vs demo

All seeded transactions, locations, route coordinates, prices, arrivals, model outputs, payment activity, and compliance rules are marked as synthetic, derived, or prototype data. The code has integrations seams for official mandi price feeds, routing providers, weather/remote sensing sources, a payment provider, and state-rule review; it does not claim live production connectivity.

See [architecture](docs/architecture.md), [API guide](docs/api.md), [data and ML plan](docs/data-and-ml.md), and [routing notes](docs/routing.md).
