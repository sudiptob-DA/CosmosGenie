# 🔭 CosmosGenie

<p align="center">
  <img
    src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Webb%27s_First_Deep_Field_%28adjusted%29.jpg/1024px-Webb%27s_First_Deep_Field_%28adjusted%29.jpg"
    alt="JWST First Deep Field" width="720"
  />
  <br/>
  <sub><i>🔭 James Webb Space Telescope — First Deep Field · NASA / ESA / CSA · Public Domain</i></sub>
</p>

> Your universe, answered. A Genie-powered astronomy assistant built on Databricks with real NASA data.

Built for the **Databricks Genie-Powered App Challenge 2026** — Track B: Creative Thinking.

## What it does

CosmosGenie lets anyone ask natural-language questions about space and get real, data-backed answers:

- *"Are any asteroids approaching Earth this week?"*
- *"When is the next blood moon?"*
- *"Where should I fly to see the 2027 solar eclipse?"*
- *"Is Artemis 2 on schedule?"*

Toggle **Kid Mode** and the same questions come back in plain language a 10-year-old can follow.
All answers come from live NASA, USNO, and JPL data stored in Delta tables, queried by Genie Agent.

---

## Architecture

```
[ Free Public APIs ]                    [ Databricks Free Edition ]

NASA NeoWs  ─────┐                      Lakeflow SDP Pipeline
NASA DONKI  ─────┤                      ┌─ bronze/ (raw API pull)
                 ├──► SDP Pipeline ────►├─ silver/ (clean + DQ expectations)
                 │                      └─ gold/   (business logic, KPIs)
USNO Moon   ─────┐
JPL / Curated ───┤
NASA Eclipse ────┼──► Lakeflow Job ────► Delta Tables (cosmos.space.*)
The Space Devs ──┤
Spaceflight News ┘
                                              │
                                    ┌─────────┴──────────┐
                                 Genie Space         AI/BI Dashboard
                                    └─────────┬──────────┘
                                         Gradio App
```

---

## Data Layer: 12 Tables · Full Medallion Architecture

### Silver Tables (source of record)

| Table | Source API | Refresh |
|---|---|---|
| `neo_close_approaches` | NASA NeoWs (free, needs key) | Daily |
| `space_weather_events` | NASA DONKI (free, needs key) | Daily |
| `moon_phases` | USNO (free, no key) | Weekly |
| `eclipse_catalog` | NASA 5-Millennium (static) | One-time |
| `eclipse_paths` | NASA curated (static) | One-time |
| `planetary_events` | Curated + JPL (free, no key) | Weekly |
| `mission_launches` | The Space Devs (free, no key) | Daily |
| `space_news` | Spaceflight News API (free, no key) | Every 6h |

### Gold Tables (analytics-ready, Genie-optimised)

| Table | Built from | What it adds |
|---|---|---|
| `gold_asteroid_alerts` | `neo_close_approaches` | threat_level (HIGH/WATCH/SAFE), miss_distance_lunar, size_estimate |
| `gold_space_weather_active` | `space_weather_events` | severity rating, aurora_likelihood per event |
| `gold_upcoming_events` | eclipses + planetary + launches | Unified 12-month timeline with days_until |
| `gold_cosmic_kpis` | All silver tables | Single-row KPI bar values — no app-side joins needed |

---

## Project Structure

```
CosmosGenie/
│
├── cosmosgenie/                          ▐ Databricks App (Gradio)
│   ├── app.py                            3-tab UI: Ask · Tonight's Sky · Mission Control
│   ├── app.yaml                          Env vars: GENIE_SPACE_ID, DASHBOARD_URL
│   └── requirements.txt                  gradio, databricks-sdk, requests
│
├── notebooks/
│   ├── setup/
│   │   └── 01_create_tables.sql          CREATE TABLE for all 8 silver Delta tables
│   │
│   ├── ingestion/                        ▐ Standalone notebooks (Lakeflow Job)
│   │   ├── ingest_asteroids.py           NASA NeoWs → MERGE upsert, daily
│   │   ├── ingest_space_weather.py       NASA DONKI FLR+GST → MERGE, daily
│   │   ├── ingest_moon_phases.py         USNO API → MERGE, weekly
│   │   ├── ingest_mission_launches.py    The Space Devs → MERGE upsert, daily
│   │   ├── ingest_space_news.py          Spaceflight News → MERGE, every 6h
│   │   ├── load_eclipse_catalog.py       NASA 5-Millennium → one-time static load
│   │   ├── load_eclipse_paths.py         City-level totality data → one-time load
│   │   └── load_planetary_events.py      Conjunctions & showers → one-time load
│   │
│   └── pipelines/                        ▐ Lakeflow Spark Declarative Pipeline (SDP)
│       ├── bronze/
│       │   ├── neo_close_approaches.py   Raw API pull → materialized view
│       │   └── space_weather_events.py   Raw API pull → materialized view
│       ├── silver/
│       │   ├── neo_close_approaches.py   Cleaned + typed + DQ expectations
│       │   └── space_weather_events.py   Cleaned + typed + DQ expectations
│       └── gold/
│           ├── asteroid_alerts.py        Threat levels + lunar distances
│           ├── space_weather_active.py   Severity + aurora likelihood
│           ├── upcoming_events.py        Unified 12-month event timeline
│           └── cosmic_kpis.py            Single-row app KPI summary
│
└── assets/
    └── cosmosgenie_demo.html             Interactive prototype (61K)
```

> **Two ingestion paths by design:** `ingestion/` notebooks are standalone scripts scheduled
> via Lakeflow Job. `pipelines/` is a Spark Declarative Pipeline with bronze → silver → gold
> and built-in DQ expectations — demonstrating both Databricks features for the hackathon.

---

## API Keys

### NASA API (required for asteroids + space weather)

1. Go to **[api.nasa.gov](https://api.nasa.gov)** → fill name + email → click **Signup**
2. Your key arrives by email within seconds: `aB3dEfGhIjKlMnOpQrStUvWxYz1234567890`
3. Free forever — 1,000 requests/day

> **No key yet?** Use `DEMO_KEY` for quick testing (30 req/hour).

### Other APIs — no key needed

| API | Used for | Limit |
|---|---|---|
| USNO (usno.navy.mil) | Moon phases | Unlimited |
| The Space Devs (ll.thespacedevs.com) | Mission launches | 15 req/hr |
| Spaceflight News (spaceflightnewsapi.net) | Breaking news | Unlimited |
| NASA Eclipse Catalog | Eclipse static data | Static file |

---

## Setup Guide

### Step 1 — Create the Delta tables

Open `notebooks/setup/01_create_tables.sql` and run it. This creates the `cosmos` catalog,
`space` schema, and all 8 silver tables.

### Step 2 — Store your NASA API key

```sh
databricks secrets create-scope cosmos
databricks secrets put-secret cosmos nasa_api_key --string-value YOUR_KEY_HERE
```

### Step 3 — Load static tables (one-time, no API key needed)

Run these three notebooks in order:
```
notebooks/ingestion/load_eclipse_catalog.py
notebooks/ingestion/load_eclipse_paths.py
notebooks/ingestion/load_planetary_events.py
```

### Step 4 — Run the live ingestion notebooks

Run once manually to seed the tables before scheduling:
```
notebooks/ingestion/ingest_asteroids.py
notebooks/ingestion/ingest_space_weather.py
notebooks/ingestion/ingest_moon_phases.py
notebooks/ingestion/ingest_mission_launches.py
notebooks/ingestion/ingest_space_news.py
```

### Step 5 — Create the Lakeflow SDP Pipeline

This builds the bronze → silver → gold medallion for asteroids and space weather.

1. Left nav → **Pipelines** → **Create pipeline** → **ETL pipeline**
2. Set:

| Field | Value |
|---|---|
| Pipeline name | `CosmosGenie Daily Ingest` |
| Serverless | On |
| Source code | `notebooks/pipelines/` (all subfolders: bronze/, silver/, gold/) |
| Target catalog | `cosmos` |
| Target schema | `space` |

3. Under **Configuration**, add:

| Key | Value |
|---|---|
| `nasa_api_key` | `{{secrets/cosmos/nasa_api_key}}` |

4. Click **Create** → click **Start** for first run

The pipeline DAG will show: bronze → silver → gold with DQ expectations on each silver table.

### Step 6 — Schedule automated refreshes (Lakeflow Jobs)

Create two jobs:

**Job 1 — CosmosGenie Daily Refresh** (runs at 06:00 UTC daily)

| Task | Notebook | Schedule |
|---|---|---|
| asteroids | `ingest_asteroids.py` | Daily 06:00 UTC |
| space_weather | `ingest_space_weather.py` | Daily 06:00 UTC |
| moon_phases | `ingest_moon_phases.py` | Daily 06:00 UTC |
| mission_launches | `ingest_mission_launches.py` | Daily 06:00 UTC |

Then trigger the SDP pipeline on completion of the above job.

**Job 2 — CosmosGenie News Refresh** (every 6 hours)

| Task | Notebook | Schedule |
|---|---|---|
| space_news | `ingest_space_news.py` | Every 6h |

To create a job: Left nav → **Jobs** → **Create job** → add tasks → set schedule.

### Step 7 — Create the Genie Space

1. Left nav → **Genie** → **New Genie Space**
2. Name: `CosmosGenie`
3. Add all 12 tables from `cosmos.space` (8 silver + 4 gold)
4. Paste these instructions:

```
- Prefer gold_* tables for user-facing questions — threat levels, severity, and
  timelines are pre-computed. Use silver tables only for detailed historical queries.
- gold_cosmic_kpis has exactly one row — use it for count/summary questions
- gold_upcoming_events joins eclipses + planetary + launches — use for "what's
  happening in space this month" queries
- Asteroid distances: always express in lunar distances (1 LD = 0.00257 AU)
- Blood Moon = eclipse_type = 'Total' AND body = 'Lunar'
- Potentially hazardous = is_potentially_hazardous = true
- Geomagnetic storm scale: G1 (minor) → G5 (extreme); stored in class_type
- is_crewed = true means humans aboard; is_moon_mission = true targets the Moon
- Eclipse travel: rank cities by sky_clarity_pct DESC, always mention totality duration
- Use plain, friendly language. Never recommend travel without stating sky_clarity_pct.
```

5. Add sample questions:
   - "Are any asteroids approaching Earth in the next 7 days?"
   - "When is the next blood moon and how long does totality last?"
   - "Where should I fly to see the 2027 total solar eclipse?"
   - "What solar flares occurred this month and how strong were they?"
   - "Is Artemis 2 still on schedule for launch?"
   - "What meteor showers are coming up?"
   - "Which city has the best chance of clear skies for the 2028 eclipse?"
   - "How many potentially hazardous asteroids are being tracked right now?"

6. Click **Save** → copy the **Space ID** from the URL (`01xxxxxxxxxxxxxxxx`)
7. Paste into `cosmosgenie/app.yaml`:
   ```yaml
   env:
     - name: GENIE_SPACE_ID
       value: "YOUR_SPACE_ID_HERE"
   ```

### Step 8 — Deploy the app

```sh
cd cosmosgenie/
databricks apps deploy
```

---

## Personal Story

Built for my son who asked me one evening if any asteroids were going to hit Earth.
Now he can ask the app himself — and get a real, data-backed answer in plain English.
Toggle Kid Mode and the same answers come back in language a 10-year-old can follow. 🚀

---
*Built with Databricks Free Edition · NASA APIs · Genie Agent · Gradio*
