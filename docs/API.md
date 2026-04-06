# API specification

The machine-readable contract is **[OpenAPI 3](openapi.json)** (generated from the FastAPI app).

## Generate / refresh

From the repo root (Python env with dependencies installed):

```bash
python scripts/export_openapi.py
```

This writes `docs/openapi.json`. It uses `DEBUG=false` so **debug-only** routes are excluded from the published schema.

## Interactive docs (running server)

| Resource        | Path            |
|----------------|-----------------|
| Swagger UI     | `/docs`         |
| ReDoc          | `/redoc`        |
| OpenAPI JSON   | `/openapi.json` |
| Alias          | `/swagger` → `/docs` |

## Route map (prefix `/api/v1`)

| Area | Router | Examples |
|------|--------|----------|
| Health | (no prefix) | `GET /health`, `/health/ready`, `/health/live` |
| Legacy AWS instances | `instances` | `GET /instances`, `GET /instances/{type}` |
| Legacy AWS pricing | `pricing` | `GET /pricing/on-demand/{type}`, `GET /pricing/compare/{type}` |
| Recommendations | `recommendations` | `POST /recommendations`, `GET /recommendations/workload-types` |
| Multi-cloud | `multicloud` | `GET /multicloud/instances`, `POST /multicloud/recommendations`, `GET /multicloud/providers` |
| CloudCost AI | `ai` | `POST /ai/chat`, `POST /ai/recommend`, `GET /ai/suggestions` |
| Spot Intelligence | `spot-intelligence` | `POST /spot-intelligence/analyze`, `GET /spot-intelligence/quick-check` |

**Request/response bodies:** Every operation in `openapi.json` includes `parameters`, `requestBody`, and `responses` with JSON schemas. Use Swagger UI for “Try it out” against a running API.
