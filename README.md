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

All answers come from live NASA, USNO, and JPL data stored in Databricks Delta tables, queried by Genie Agent.

## Architecture

```
[ Free Public APIs ]              [ Databricks Free Edition ]
NASA NeoWs  ──────────┐
NASA DONKI  ──────────┤
USNO Moon   ──────────┼──► Lakeflow Job ──► Delta Tables (cosmos.space.*)
JPL / Curated ────────┤                            │
NASA Eclipse CSV ─────┘                    ┌───────┴────────┐
The Space Devs ───────┘               Genie Space    AI/BI Dashboard
Spaceflight News ─────┘                    │                │
                                      Databricks App (Gradio)
```

## Tables (8 total)

| Table | Source | Refresh |
|---|---|---|
| `neo_close_approaches` | NASA NeoWs | Daily |
| `space_weather_events` | NASA DONKI | Daily |
| `moon_phases` | USNO | Weekly |
| `eclipse_catalog` | NASA 5-Millennium | Static |
| `planetary_events` | Curated + JPL | Weekly |
| `mission_launches` | The Space Devs | Daily |
| `space_news` | Spaceflight News API | Every 6h |
| `eclipse_paths` | NASA curated | Static |

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
│   │   └── 01_create_tables.sql          CREATE TABLE for all 8 Delta tables
│   │
│   ├── ingestion/                        ▐ Standalone notebooks (run via Lakeflow Job)
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
│       └── README.md                     Pipeline setup & expectation reference
│
└── assets/
    └── cosmosgenie_demo.html             Interactive prototype (animated galaxy,
                                              3 tabs, 6 QA pairs, Kid Mode toggle,
                                              rocket launch Easter egg — 61K)
```

> **Two ingestion paths by design:** The `ingestion/` notebooks are standalone scripts
> scheduled via a Lakeflow Job. The `pipelines/` folder is a Spark Declarative Pipeline
> (bronze → silver) with built-in data quality expectations — demonstrating both
> Databricks features for the hackathon submission.

## API Keys

### NASA API (required for asteroids + space weather)

1. Go to **[api.nasa.gov](https://api.nasa.gov)**
2. Fill in your first name, last name, and email — click **Signup**
3. Your key arrives by email within seconds. It looks like: `aB3dEfGhIjKlMnOpQrStUvWxYz1234567890`
4. Free forever — 1,000 requests/day (more than enough for daily refresh)

> **No key yet?** Use `DEMO_KEY` for quick testing (30 req/hour).
> Substitute it anywhere you see `YOUR_KEY_HERE` in the notebooks.

### Other APIs — no key needed

| API | Used for | Limit |
|---|---|---|
| USNO (usno.navy.mil) | Moon phases | No limit |
| The Space Devs (ll.thespacedevs.com) | Mission launches | 15 req/hr |
| Spaceflight News API (spaceflightnewsapi.net) | Breaking news | No limit |
| NASA Eclipse Catalog | Eclipse data | Static CSV |

## Setup

1. Run `notebooks/setup/01_create_tables.sql` to create all 8 Delta tables
2. Run the one-time load notebooks (`load_eclipse_catalog`, `load_eclipse_paths`, `load_planetary_events`)
3. Register at [api.nasa.gov](https://api.nasa.gov), get your free key, then store it:
   ```sh
   databricks secrets create-scope cosmos
   databricks secrets put-secret cosmos nasa_api_key --string-value YOUR_KEY_HERE
   ```
4. Schedule `CosmosGenie Daily Refresh` Lakeflow Job with the ingestion notebooks
5. Create a Genie Space with all 8 tables — copy the Space ID into `app.yaml`
6. Deploy the app from the `cosmosgenie/` folder


## Creating the Genie Space

The Genie Space is the brain of CosmosGenie — it translates natural language questions
into SQL over your 8 Delta tables.

### Steps

1. In your Databricks workspace, go to **left nav → Genie → New Genie Space**
2. Name it `CosmosGenie`
3. Under **Tables**, add all 8 tables from `cosmos.space`:
   - `neo_close_approaches`, `space_weather_events`, `moon_phases`
   - `eclipse_catalog`, `eclipse_paths`, `planetary_events`
   - `mission_launches`, `space_news`

4. Under **Instructions**, paste the following:

```
- Asteroid distances: always contextualize in lunar distances (1 LD = 0.00257 AU)
- Blood Moon = eclipse_type = 'Total' AND body = 'Lunar'
- Potentially hazardous asteroids = is_potentially_hazardous = true
- Geomagnetic storm scale: G1 (minor) to G5 (extreme); class_type stores the G-scale
- is_crewed = true means humans are aboard; is_moon_mission = true means it targets the Moon
- For eclipse travel queries: rank cities by sky_clarity_pct DESC, mention totality duration
- Use plain, friendly language; avoid jargon unless asked
- Never recommend travel to a location without mentioning the sky_clarity_pct risk
```

5. Add a few **sample questions** to help Genie learn your intent:
   - "Are any asteroids approaching Earth in the next 7 days?"
   - "When is the next blood moon and how long does totality last?"
   - "Where should I fly to see the 2027 total solar eclipse?"
   - "What solar flares occurred this month and how strong were they?"
   - "Is Artemis 2 still on schedule for launch?"
   - "What planetary conjunctions are coming up in the next 6 months?"
   - "Which city has the best chance of clear skies for the 2028 eclipse?"
   - "How many potentially hazardous asteroids are currently being tracked?"

6. Click **Save**, then copy the **Space ID** from the browser URL
   - Format: `01xxxxxxxxxxxxxxxx` (e.g. `01ef8a3c2d1b4f9e`)

7. Paste it into `cosmosgenie/app.yaml`:
   ```yaml
   env:
     - name: GENIE_SPACE_ID
       value: "YOUR_SPACE_ID_HERE"   # ← paste here
   ```

> **Tip:** Test the space directly in the Genie UI before deploying the app.
> Ask it a few questions from the list above to confirm it's querying the right tables.

## Personal Story

Built for my son who asked me one evening if any asteroids were going to hit Earth.
Now he can ask the app himself — and get a real, data-backed answer in plain English. 🚀

---
*Built with Databricks Free Edition · NASA APIs · Genie Agent · Gradio*
