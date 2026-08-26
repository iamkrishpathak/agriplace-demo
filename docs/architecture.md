# Architecture

```text
Static responsive SPA (frontend/)
           | REST + JWT
FastAPI (backend/app/main.py)
           |
SQLAlchemy domain model + SQLite demo database
           |
market intelligence | matching | routing | workflows | audit
```

## Product surfaces

The frontend is deliberately a lightweight static SPA for a reliable hackathon demo. It contains four working role workspaces:

- Farmer: bilingual greeting, mandi price range, sale estimate, listing view, alerts, payment protection state.
- Buyer: marketplace filters, requirement form, explainable matching result, protected orders.
- Transporter: route visualization, trip acceptance, capacity-aware optimization, pickup proof state.
- Admin: system KPI view, matching weight controls, AI signal labels, audit stream.

The SPA is API-first, so it can be moved to Next.js route components without changing the backend contract. `frontend/app.js` uses only browser APIs to keep startup fast and installation-free for the prototype.

## Backend modules

| Module | Responsibility |
| --- | --- |
| `main.py` | FastAPI routes, auth dependencies, serialization, consistent response envelope |
| `models.py` | Normalized marketplace, order, payment, delivery, reputation, data-source and audit entities |
| `services/market_intelligence.py` | Price and demand baseline signals, sale estimate breakdown, alerts |
| `services/matching.py` | Quantity, quality, distance, price, availability and reliability scoring |
| `services/routing.py` | OR-Tools CVRP solver using an explicit derived distance matrix |
| `services/workflows.py` | Order creation, hold simulation, delivery setup and route persistence |
| `seed.py` | Repeatable Nashik-to-Mumbai demo scenario |

## Core workflow

1. A farmer publishes a lot with crop, grade, quantity, availability, pickup location, and expected price.
2. A buyer creates a requirement with destination, needed-by date, grade, quantity, and maximum price.
3. Matching ranks eligible lots with explicit component scores and aggregates enough supply where possible.
4. Order creation adds order items, a payment hold, route and delivery records, and audit events in one database transaction.
5. A transporter accepts a requested delivery, receives an OR-Tools route, and submits pickup proof per stop.
6. Buyer confirmation releases all or part of the held value; rejection or partial acceptance opens a dispute state.

## Security and operational controls

- Password hashes use PBKDF2-SHA256 and JWT tokens carry the authenticated subject and roles.
- Route, buyer, farmer, transporter, and admin endpoints enforce role authorization.
- Write actions record actor, entity, old/new payload where appropriate, and timestamp in `audit_logs`.
- Data sources include classification metadata; user-facing surfaces call synthetic and derived demo values out plainly.
- Production deployment should replace SQLite with PostgreSQL, configure a unique secret in environment variables, add migrations, and put authenticated HTTPS/API-rate limiting in front of the service.
