# GitHub Pages (frontend only)

The React UI is built with `base: /cloudcost-optimizer/` for **project Pages**:

**Live URL:** `https://<your-github-username>.github.io/cloudcost-optimizer/`

## Swagger UI (API docs on Render)

The backend is FastAPI. Open interactive docs on your API host, for example:

- **Swagger UI:** `https://<your-api-host>/docs` (alias: `/swagger` → redirects to `/docs`)
- **ReDoc:** `https://<your-api-host>/redoc`
- **OpenAPI JSON:** `https://<your-api-host>/openapi.json`

Replace `<your-api-host>` with your Render URL (e.g. `cloudcost-api-3uy5.onrender.com`).

## One-time setup

1. **Repo → Settings → Pages**
   - **Source:** GitHub Actions (not “Deploy from branch”).
2. **Render API → Environment**
   - Set **`CORS_ORIGINS`** to include your Pages origin, comma-separated, **no spaces**, e.g.  
     `https://kadaliaswinkumar.github.io,http://localhost:8080,...`  
   - Browsers send origin `https://username.github.io` (no path); the path `/cloudcost-optimizer` does not appear in CORS.

## API URL for the static build

- **Default:** The workflow uses `https://cloudcost-api-3uy5.onrender.com` if you set nothing else.
- **Override:** Repository **Settings → Secrets and variables → Actions → Variables** → create **`VITE_API_URL`** with your Render API URL, then re-run the workflow.

## Deploy

- Push to **`main`** (changes under `frontend/` or the workflow file), or run **Actions → Deploy to GitHub Pages → Run workflow**.

## If the site is blank

- Confirm the workflow finished green and Pages shows the latest deployment.
- Open DevTools → Network: API calls should go to your Render host (not `localhost`).
- Fix CORS on the API if requests are blocked.
