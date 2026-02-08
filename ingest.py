#!/usr/bin/env python3

"""
OpenSky Flight Tracker - Ingest

Polls OpenSky /api/states/all for a geofenced bounding box and UPSERTs the latest
aircraft state into PostgreSQL.
"""


import os
import time
import requests
import psycopg2
from psycopg2.extras import execute_values

STATES_URL = "https://opensky-network.org/api/states/all"
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

UPSERT_SQL = """
INSERT INTO aircraft_states (
  icao24, callsign, origin_country,
  longitude, latitude, baro_altitude, on_ground,
  velocity, true_track, vertical_rate,
  geo_altitude, squawk, spi
)
VALUES %s
ON CONFLICT (icao24) DO UPDATE SET
  callsign       = EXCLUDED.callsign,
  origin_country = EXCLUDED.origin_country,
  longitude      = EXCLUDED.longitude,
  latitude       = EXCLUDED.latitude,
  baro_altitude  = EXCLUDED.baro_altitude,
  on_ground      = EXCLUDED.on_ground,
  velocity       = EXCLUDED.velocity,
  true_track     = EXCLUDED.true_track,
  vertical_rate  = EXCLUDED.vertical_rate,
  geo_altitude   = EXCLUDED.geo_altitude,
  squawk         = EXCLUDED.squawk,
  spi            = EXCLUDED.spi,
  updated_at     = now();
"""


PRUNE_SQL = """
DELETE FROM aircraft_states
WHERE icao24 IN (
  SELECT icao24
  FROM aircraft_states
  ORDER BY updated_at DESC
  OFFSET %(max_rows)s
);
"""

def get_env(name, default=None):
    val = os.environ.get(name)
    if val is None:
        return default
    return val

def pg_connect():
    return psycopg2.connect(
        host=get_env("PGHOST", "localhost"),
        port=get_env("PGPORT", "5432"),
        dbname=get_env("PGDATABASE", "flightlogs"),
        user=get_env("PGUSER", "flightview"),
        password=get_env("PGPASSWORD", "flightview"),
    )

def get_token(session, client_id, client_secret):
    """Get an OAuth2 access token from OpenSky."""
    r = session.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=10,
    )
    r.raise_for_status()
    j = r.json()
    return j["access_token"]

def parse_state_to_row(state):
    """
    Convert one OpenSky "state vector" list into a tuple matching our SQL columns.

    OpenSky returns a list with fixed positions:
    [0]=icao24, [1]=callsign, [2]=origin_country, [5]=longitude, [6]=latitude, etc.
    """
    if not state or len(state) < 16:
        return None

    icao24 = state[0]
    if not icao24:
        return None

    callsign = state[1]
    if isinstance(callsign, str):
        callsign = callsign.strip()  # remove trailing spaces

    return (
        icao24,
        callsign or None,
        state[2],   # origin_country
        state[5],   # longitude
        state[6],   # latitude
        state[7],   # baro_altitude
        state[8],   # on_ground
        state[9],   # velocity
        state[10],  # true_track
        state[11],  # vertical_rate
        state[13],  # geo_altitude
        state[14],  # squawk
        state[15],  # spi
    )

def main():
    client_id = os.environ["OPENSKY_CLIENT_ID"]
    client_secret = os.environ["OPENSKY_CLIENT_SECRET"]

    # PHX-ish defaults (you can override with env vars)
    lamin = float(get_env("GEOFENCE_LAMIN", "33.386590"))
    lomin = float(get_env("GEOFENCE_LOMIN", "-112.036858"))
    lamax = float(get_env("GEOFENCE_LAMAX", "33.444190"))
    lomax = float(get_env("GEOFENCE_LOMAX", "-111.893005"))

    poll_seconds = int(get_env("POLL_SECONDS", "30"))
    max_rows = int(get_env("MAX_ROWS", "100"))

    params = {"lamin": lamin, "lomin": lomin, "lamax": lamax, "lomax": lomax}

    session = requests.Session()
    token = get_token(session, client_id, client_secret)

    while True:
        try:
            # Use the bearer token
            headers = {"Authorization": f"Bearer {token}"}
            r = session.get(STATES_URL, params=params, headers=headers, timeout=10)

            # If token expires/gets rejected, refresh and retry once
            if r.status_code == 401:
                print("Got 401 (token expired?). Refreshing token...")
                token = get_token(session, client_id, client_secret)
                headers = {"Authorization": f"Bearer {token}"}
                r = session.get(STATES_URL, params=params, headers=headers, timeout=10)

            # If rate limited, pause (simple approach)
            if r.status_code == 429:
                print("Rate limited (429). Sleeping 60s then retrying...")
                time.sleep(60)
                continue

            r.raise_for_status()
            data = r.json()

            states = data.get("states")
            if states is None:
                print("No states returned (states=null).")
                time.sleep(poll_seconds)
                continue

            rows = []
            for s in states:
                row = parse_state_to_row(s)
                if row is not None:
                    rows.append(row)

            # Write to Postgres
            if rows:
                conn = pg_connect()
                with conn:
                    with conn.cursor() as cur:
                        execute_values(cur, UPSERT_SQL, rows, page_size=1000)

                        # Optional pruning: keep only latest N rows
                        if max_rows > 0:
                            cur.execute(PRUNE_SQL, {"max_rows": max_rows})
                conn.close()

            print(f"Upserted {len(rows)} aircraft rows.")
            time.sleep(poll_seconds)

        except Exception as e:
            # Keep it simple: log the error, wait a minute, try again
            print("ERROR:", e)
            print("Sleeping 60s then continuing...")
            time.sleep(60)

if __name__ == "__main__":
    main()
