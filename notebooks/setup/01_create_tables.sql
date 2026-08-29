-- Databricks notebook source
-- MAGIC %md
-- MAGIC # CosmosGenie — Create Delta Tables
-- MAGIC Run this once to initialise all 8 tables in the `cosmos.space` schema.

-- COMMAND ----------
CREATE CATALOG IF NOT EXISTS cosmos;
CREATE SCHEMA  IF NOT EXISTS cosmos.space;

-- COMMAND ----------
-- 1. Asteroid close approaches
CREATE TABLE IF NOT EXISTS cosmos.space.neo_close_approaches (
  asteroid_id              STRING  COMMENT 'NASA SPK-ID',
  name                     STRING  COMMENT 'Asteroid designation',
  approach_date            DATE    COMMENT 'Date of closest approach',
  miss_distance_au         DOUBLE  COMMENT 'Miss distance in Astronomical Units',
  miss_distance_km         DOUBLE  COMMENT 'Miss distance in kilometers',
  velocity_kps             DOUBLE  COMMENT 'Relative velocity km/s',
  diameter_min_m           DOUBLE  COMMENT 'Estimated minimum diameter in meters',
  diameter_max_m           DOUBLE  COMMENT 'Estimated maximum diameter in meters',
  is_potentially_hazardous BOOLEAN COMMENT 'NASA PHA flag',
  absolute_magnitude       DOUBLE  COMMENT 'Absolute magnitude H',
  fetched_at               TIMESTAMP
) USING DELTA COMMENT 'NASA NeoWs asteroid close approach data — refreshed daily';

-- COMMAND ----------
-- 2. Space weather events
CREATE TABLE IF NOT EXISTS cosmos.space.space_weather_events (
  event_id      STRING    COMMENT 'Unique DONKI event identifier',
  event_type    STRING    COMMENT 'FLR=Solar Flare, GST=Geomagnetic Storm',
  begin_time    TIMESTAMP,
  peak_time     TIMESTAMP,
  end_time      TIMESTAMP,
  class_type    STRING    COMMENT 'e.g. X2.1, G2',
  active_region INT       COMMENT 'NOAA active region number',
  kp_index      DOUBLE    COMMENT 'Kp index (GST only)',
  fetched_at    TIMESTAMP
) USING DELTA COMMENT 'NASA DONKI space weather — refreshed daily';

-- COMMAND ----------
-- 3. Moon phases
CREATE TABLE IF NOT EXISTS cosmos.space.moon_phases (
  phase_date   DATE    COMMENT 'Date of the moon phase',
  phase_time   STRING  COMMENT 'UTC time of phase',
  phase_name   STRING  COMMENT 'New Moon / First Quarter / Full Moon / Last Quarter',
  year         INT,
  is_supermoon BOOLEAN,
  fetched_at   TIMESTAMP
) USING DELTA COMMENT 'USNO moon phase calendar — refreshed weekly';

-- COMMAND ----------
-- 4. Eclipse catalog
CREATE TABLE IF NOT EXISTS cosmos.space.eclipse_catalog (
  eclipse_date     DATE   COMMENT 'Date of eclipse',
  eclipse_type     STRING COMMENT 'Total / Partial / Annular / Hybrid / Penumbral',
  body             STRING COMMENT 'Solar or Lunar',
  duration_minutes DOUBLE COMMENT 'Duration of totality in minutes',
  path_description STRING COMMENT 'Geographic visibility region',
  gamma            DOUBLE,
  magnitude        DOUBLE,
  year             INT
) USING DELTA COMMENT 'NASA 5-Millennium Eclipse Catalog — static';

-- COMMAND ----------
-- 5. Planetary events
CREATE TABLE IF NOT EXISTS cosmos.space.planetary_events (
  event_date             DATE   COMMENT 'Date of the event',
  event_type             STRING COMMENT 'Conjunction / Opposition / Meteor Shower / Alignment',
  primary_body           STRING,
  secondary_body         STRING,
  angular_separation_deg DOUBLE,
  visibility             STRING,
  description            STRING,
  year                   INT
) USING DELTA COMMENT 'Planetary conjunctions, oppositions, alignments, meteor showers';

-- COMMAND ----------
-- 6. Mission launches
CREATE TABLE IF NOT EXISTS cosmos.space.mission_launches (
  launch_id           STRING    COMMENT 'Unique ID from The Space Devs',
  name                STRING,
  launch_date         TIMESTAMP COMMENT 'No Earlier Than (NET) date UTC',
  status              STRING    COMMENT 'Go / TBD / Hold',
  agency              STRING,
  agency_country      STRING,
  rocket              STRING,
  mission_name        STRING,
  mission_description STRING,
  mission_type        STRING,
  launch_site         STRING,
  launch_site_country STRING,
  is_crewed           BOOLEAN   COMMENT 'True if humans are aboard',
  is_moon_mission     BOOLEAN   COMMENT 'True if targets the Moon',
  webcast_url         STRING,
  fetched_at          TIMESTAMP
) USING DELTA COMMENT 'The Space Devs API — refreshed daily';

-- COMMAND ----------
-- 7. Space news
CREATE TABLE IF NOT EXISTS cosmos.space.space_news (
  article_id   STRING,
  title        STRING,
  summary      STRING,
  url          STRING,
  image_url    STRING,
  news_site    STRING,
  published_at TIMESTAMP,
  is_featured  BOOLEAN,
  fetched_at   TIMESTAMP
) USING DELTA COMMENT 'Spaceflight News API — refreshed every 6 hours';

-- COMMAND ----------
-- 8. Eclipse paths
CREATE TABLE IF NOT EXISTS cosmos.space.eclipse_paths (
  eclipse_date            DATE    COMMENT 'Date of the total solar eclipse',
  city_name               STRING,
  country                 STRING,
  region                  STRING,
  latitude                DOUBLE,
  longitude               DOUBLE,
  totality_duration_sec   INT     COMMENT 'Duration of totality in seconds',
  dist_from_centerline_km INT     COMMENT '0 = maximum totality',
  nearest_airport_code    STRING  COMMENT 'IATA airport code',
  sky_clarity_pct         INT     COMMENT 'Historical clear-sky probability 0-100',
  viewing_notes           STRING
) USING DELTA COMMENT 'City-level eclipse totality viewing data — curated from NASA eclipse paths';

-- COMMAND ----------
SELECT 'All 8 tables created successfully' AS status;
