# OpenSky Flight Tracker (Geofenced Airspace)

Python project that polls the OpenSky REST API every ~30 seconds, filters aircraft inside a geofence (default: PHX bounding box), and stores the latest aircraft state in PostgreSQL using UPSERT (no duplicates).

## Features
- Geofence bounding box (env-configurable)
- Stores "current aircraft state" keyed by `icao24`
- Terminal viewer reads from Postgres (safe for SSH ForceCommand viewer-only access)
- systemd service file included for Raspberry Pi deployment

## Tech
Python, requests, PostgreSQL, Linux/systemd, SSH

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your OpenSky credentials
set -a; source .env; set +a

psql "postgresql://$PGUSER:$PGPASSWORD@$PGHOST:$PGPORT/$PGDATABASE" -f sql/schema.sql

python ingest.py
python viewer.py
```
##SSH viewer-only mode (ForceCommand)
See `docs/ssh_forcecommand.md`.
