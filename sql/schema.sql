-- Simple table that stores "latest known state" per aircraft (icao24 is unique)
CREATE TABLE IF NOT EXISTS aircraft_states (
  icao24          TEXT PRIMARY KEY,
  callsign        TEXT,
  origin_country  TEXT,
  longitude       DOUBLE PRECISION,
  latitude        DOUBLE PRECISION,
  baro_altitude   DOUBLE PRECISION,
  on_ground       BOOLEAN,
  velocity        DOUBLE PRECISION,
  true_track      DOUBLE PRECISION,
  vertical_rate   DOUBLE PRECISION,
  geo_altitude    DOUBLE PRECISION,
  squawk          TEXT,
  spi             BOOLEAN,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS aircraft_states_updated_at_idx
  ON aircraft_states (updated_at DESC);
