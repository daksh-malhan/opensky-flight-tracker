#!/usr/bin/env python3
"""
OpenSky Flight Tracker - Viewer

Reads the latest aircraft states from Postgres and prints them in a simple terminal view.
"""
import os
import time
from zoneinfo import ZoneInfo
import psycopg2

EXTRACT_SQL = """
SELECT
  icao24, callsign, origin_country,
  longitude, latitude, baro_altitude, on_ground,
  velocity, true_track, vertical_rate,
  geo_altitude, squawk, spi,
  updated_at
FROM aircraft_states
ORDER BY updated_at DESC
LIMIT %(limit)s;
"""

def get_env(name, default=None):
    v = os.environ.get(name)
    return default if v is None else v

def pg_connect():
    return psycopg2.connect(
        host=get_env("PGHOST", "localhost"),
        port=get_env("PGPORT", "5432"),
        dbname=get_env("PGDATABASE", "flightlogs"),
        user=get_env("PGUSER", "flightview"),
        password=get_env("PGPASSWORD", "flightview"),
    )

def clear_screen():
    # Works well in SSH terminals
    print("\033[2J\033[H", end="")

def main():
    limit = int(get_env("VIEW_LIMIT", "10"))
    refresh = int(get_env("VIEW_REFRESH", "5"))
    tz = get_env("VIEW_TZ", "America/Phoenix")

    while True:
        conn = pg_connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute(EXTRACT_SQL, {"limit": limit})
                rows = cur.fetchall()
        conn.close()

        clear_screen()
        print(f"Most recent aircraft (limit={limit})\n")

        for row in rows:
            row = list(row)
            row[-1] = row[-1].astimezone(ZoneInfo(tz)).strftime("%b %d, %Y %I:%M %p")
            print(row)

        time.sleep(refresh)

if __name__ == "__main__":
    main()
