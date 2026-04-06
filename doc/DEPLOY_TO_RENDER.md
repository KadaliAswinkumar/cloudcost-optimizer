# Deploy to Render (Free Tier)

Everything runs on **Render only**: web API, static frontend, and PostgreSQL. **No Redis, Upstash, or Fly.io** is required. If `REDIS_URL` is not set, the API skips caching and uses in-memory rate-limit behavior (already supported in code).

## Why Render

- Free tier available; Git push can auto-deploy
- PostgreSQL included on free tier (see Render’s current limits)
- `render.yaml` in the repo defines the blueprint (API + static site + DB + cron)

---

## Fast path: Blueprint from GitHub

1. Push this repo to GitHub (branch `main`).
2. Sign in at [render.com](https://render.com) with GitHub.
3. **New +** → **Blueprint** → select **`cloudcost-optimizer`**.
4. Apply. Render creates **`cloudcost-db`**, **`cloudcost-api`**, **`cloudcost-app`**, and the **`spot-price-collector`** cron from [`render.yaml`](../render.yaml).

### Environment variables to set in the dashboard (if not already in the blueprint)

| Service | Variable | Notes |
|--------|----------|--------|
| **cloudcost-api** | `GROQ_API_KEY` | For CloudCost AI chat ([Groq keys](https://console.groq.com/keys)). |
| **cloudcost-api** | `CORS_ORIGINS` | Comma-separated, **no spaces**. Include your real frontend URL, e.g. `https://cloudcost-app.onrender.com` and any local dev URLs you use. |
| **cloudcost-app** | `VITE_API_URL` | Must match your API URL, e.g. `https://cloudcost-api.onrender.com`. Rebuild the static site after changing this. |

`DATABASE_URL` and `SECRET_KEY` are wired in the blueprint. **Do not** add Redis unless you want it.

If Render assigns different service names than `cloudcost-api` / `cloudcost-app`, update `VITE_API_URL` and `CORS_ORIGINS` to match your actual `https://….onrender.com` URLs.

---

## Manual path (same app, created by hand)

1. **PostgreSQL**: **New +** → **PostgreSQL** — note the internal connection string.
2. **Web service** (Python): repo root, build `pip install --upgrade pip && pip install -r requirements.txt`, start `alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`. Add `DATABASE_URL`, `SECRET_KEY`, `ENVIRONMENT=production`, `DEBUG=false`, `CORS_ORIGINS`, `GROQ_API_KEY` (optional but needed for AI).
3. **Static site**: root dir `frontend`, build `npm install && npm run build`, publish `dist`, env `VITE_API_URL=<your API URL>`.
4. Point `CORS_ORIGINS` at your static site URL.

---

## After deploy

```bash
curl https://<your-api-host>/health
```

Open the static URL, sign up / log in, and confirm API calls succeed (browser devtools → Network).

Auto-deploy: enable “auto-deploy” on `main` in each service’s settings if you want every push to rebuild.

---

## Free tier notes

- Web services may **sleep** after idle time; first request can be slow.
- PostgreSQL free tier limits change over time — check Render’s docs.
- **No Redis**: response caching is off; the product still works.

---

## Troubleshooting

| Issue | What to check |
|--------|----------------|
| Frontend 404 / blank | `VITE_API_URL` wrong; rebuild static site after fixing. |
| CORS errors | `CORS_ORIGINS` must list the exact frontend origin (scheme + host, no trailing slash issues). |
| DB errors | `DATABASE_URL` from the same Render region; migrations ran (`alembic upgrade head` in start command). |

---

## Optional: Redis later

Only if you add a Redis instance yourself, set `REDIS_URL` on **`cloudcost-api`**. Until then, leave it unset.
