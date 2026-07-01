# ELD Trip Planner

Full-stack app (Django + React) that takes trip details — current location, pickup
location, dropoff location, and current 70-hour/8-day cycle hours used — and returns
a route map with stops/rests plus fully drawn FMCSA-style Daily Log Sheets (one per
day of the trip).

## Stack

- **Backend**: Django + Django REST Framework. A pure-Python HOS/ELD rules engine
  (`backend/apps/trips/hos/`) computes the duty-status schedule; Django only handles
  HTTP, persistence, and orchestration.
- **Geocoding/Routing**: OpenStreetMap Nominatim (geocoding) + the public OSRM demo
  server (routing). Both free, no API keys required, called server-side.
- **Map**: React + react-leaflet + OpenStreetMap tiles.
- **Daily log sheets**: rendered as SVG, matching the standard FMCSA "Driver's Daily
  Log (24 hours)" paper form layout.
- **Persistence**: a `Trip` model stores each planned trip (inputs + computed route
  and daily logs as JSON) so the UI can show trip history.

## HOS rules implemented

Property-carrying driver, 70-hour/8-day cycle, no adverse driving conditions:

- 11-hour driving limit per duty window
- 14-hour on-duty window (doesn't pause for breaks)
- 30-minute break required after 8 cumulative hours of driving
- 70-hour/8-day cycle cap, resolved via a 34-hour restart
- Fueling stop at least every 1,000 miles
- 1 hour each for pickup and dropoff (on-duty, not driving)

**Documented simplifications**: the sleeper-berth split-duty provision is out of
scope (all mandatory rest is modeled as Off Duty); the 70-hour cycle is tracked as a
single running total seeded by `current_cycle_used_hrs` rather than a true rolling
8-day window, since the app only receives a single cycle-hours snapshot as input, not
a daily breakdown of the preceding 8 days.

## Local development

### Backend

```bash
cd backend
python3 -m venv ../backend_venv       # or your preferred venv location
../backend_venv/bin/pip install -r requirements.txt
cp .env.example .env
../backend_venv/bin/python manage.py migrate
../backend_venv/bin/python manage.py runserver 8000
```

Run tests:

```bash
../backend_venv/bin/python -m pytest apps/trips/
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev   # http://localhost:5173
```

## API

- `POST /api/trips/plan/` — body: `{ current_location, pickup_location, dropoff_location, current_cycle_used_hrs, driver_name?, carrier_name?, truck_number? }`. Returns the full `Trip` object (route geometry, stops, and daily log sheets).
- `GET /api/trips/` — recent trip history.
- `GET /api/trips/<uuid>/` — full trip detail.

Error responses are shaped `{ "error": "<code>", "message": "...", "field"?: "..." }`
with HTTP 422 for bad input (unresolvable location, no drivable route) and 502 if the
geocoding/routing services are unreachable.

## Deployment

- **Backend** → [Render](https://render.com), via the `render.yaml` blueprint at the
  repo root (web service + free Postgres). Render's free web services have an
  ephemeral filesystem, so Postgres (not SQLite) is used in production.
- **Frontend** → [Vercel](https://vercel.com), root directory `frontend/`, with
  `VITE_API_URL` pointing at the deployed Render backend URL.

Steps:

1. Push this repo to GitHub.
2. On Render: New → Blueprint → select the repo. Render provisions the web service
   and database from `render.yaml` automatically.
3. On Vercel: New Project → import the repo → set root directory to `frontend/` →
   add env var `VITE_API_URL=https://<your-render-service>.onrender.com/api`.
4. Back on Render, update the `CORS_ALLOWED_ORIGINS` env var to your real Vercel
   domain, then redeploy.

## Worked examples (used for verification)

- **Short trip**: Chicago, IL → Indianapolis, IN, cycle used = 10h → single daily
  log sheet, no restart/fuel stops needed.
- **Long trip**: Los Angeles, CA → New York, NY, cycle used = 60h → forces an early
  34-hour restart, multiple fuel stops (~1000mi intervals), and 5+ daily log sheets.
