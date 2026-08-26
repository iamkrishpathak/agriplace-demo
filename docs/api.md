# API guide

Every endpoint returns:

```json
{"success": true, "data": {}, "message": null, "error": null}
```

Protected endpoints use `Authorization: Bearer <JWT>`.

| Group | Endpoints |
| --- | --- |
| Access | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `GET /demo/accounts` |
| Farmer | `GET /farmer/home`, `POST /farmer/sale-estimate`, `GET/POST /farmer/listings` |
| Buyer | `GET /buyer/marketplace`, `GET/POST /buyer/requirements`, `GET /buyer/requirements/{id}/matches`, `POST /buyer/requirements/{id}/order`, `GET /buyer/orders`, `POST /buyer/deliveries/{id}/confirm` |
| Transporter | `GET /transporter/trips/available`, `POST /transporter/trips/{id}/accept`, `GET /transporter/active`, `POST /transporter/deliveries/{id}/pickup`, `POST /transporter/deliveries/{id}/incident` |
| Intelligence | `POST /routes/optimize`, `POST /ml/price/predict`, `POST /ml/demand/predict`, `POST /ml/quality/predict`, `POST /ml/match/score` |
| Administration | `GET /admin/dashboard`, `GET/POST /admin/matching-weights`, `GET /admin/audit-logs`, `GET /admin/state-rules` |
| Discovery | `GET /health`, `GET /data/sources`, `GET /notifications`, `GET /demo/scenario` |

## Demo account emails

| Role | Email |
| --- | --- |
| Farmer | `farmer@agriplace.demo` |
| Buyer | `buyer@agriplace.demo` |
| Transporter | `transporter@agriplace.demo` |
| Admin | `admin@agriplace.demo` |

All use password `AgriPlace@123`.
