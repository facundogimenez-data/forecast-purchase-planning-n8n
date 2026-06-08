# Deploy — Streamlit Dashboard on EasyPanel

This dashboard does **not** ship its own database. It connects directly to the
MySQL instance that already backs the demo n8n workflow (the same one the
automation writes `forecasts`, `purchase_plan`, `inventory_snapshots`, and
`products` to). Deploying it is just a matter of running the container next to
that MySQL service and pointing it at the right host/credentials.

## 1. Prerequisites

- The demo n8n + MySQL stack already running in EasyPanel, with the
  `forecasts` / `purchase_plan` / `inventory_snapshots` / `products` tables
  populated (see [`../src/queries.sql`](../src/queries.sql)).
- A MySQL user with `SELECT` access to those tables (read-only is enough —
  the dashboard never writes).

## 2. Create the service in EasyPanel

1. **App → Create Service → App from Git Repository**
2. Repository: `https://github.com/facundogimenez-data/forecast-purchase-planning-n8n`
3. **Build context / root directory:** `dashboard`
4. **Build method:** Dockerfile (uses [`Dockerfile`](Dockerfile) in this folder)
5. **Port:** `8501`

## 3. Environment variables

Set these in the EasyPanel service config (mirrors [`.env.example`](.env.example)):

| Variable | Value |
|---|---|
| `DB_HOST` | Internal hostname of the MySQL service in EasyPanel (e.g. `mysql_n8n` — same project network, no need to expose it publicly) |
| `DB_PORT` | `3306` |
| `DB_USER` | Read-only MySQL user for the dashboard |
| `DB_PASSWORD` | That user's password (store as a secret, not plain text) |
| `DB_NAME` | Name of the database the n8n workflow writes to |

> If the dashboard and the MySQL instance live in **different** EasyPanel
> projects, either attach them to the same Docker network or use the public
> hostname/port EasyPanel exposes for MySQL — just make sure the connection
> isn't open to the internet without a strong password.

## 4. Networking

EasyPanel places services from the same project on a shared internal Docker
network, reachable by service name — that's what `DB_HOST` should point to.
No extra reverse-proxy config is needed beyond exposing port `8501` for the
dashboard itself (EasyPanel handles the domain/HTTPS layer).

## 5. Deploy & verify

1. Trigger the build/deploy from the EasyPanel UI.
2. Open the assigned domain — you should see the **Forecast & Purchase
   Planning** dashboard with the latest weekly data.
3. If you see *"No se pudo conectar a la base de datos"*, double-check
   `DB_HOST`/credentials and that the dashboard service can reach the MySQL
   service on the internal network (EasyPanel → service → "Network" tab).

## Local testing (optional, before deploying)

```bash
cd dashboard
cp .env.example .env   # point it at a reachable MySQL instance
docker compose -f docker-compose.prod.yml --env-file .env up --build
```

Then open http://localhost:8501.
