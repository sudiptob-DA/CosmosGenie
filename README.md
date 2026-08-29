# 🔭 CosmosGenie

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
├── cosmosgenie/          # Databricks App
│   ├── app.py            # Gradio UI + Genie integration
│   ├── app.yaml          # App config + env vars
│   └── requirements.txt
├── notebooks/
│   ├── setup/            # Table creation SQL
│   └── ingestion/        # 8 data ingestion notebooks
└── assets/
    └── cosmosgenie_demo.html   # Interactive design prototype
```

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

## Personal Story

Built for my son who asked me one evening if any asteroids were going to hit Earth.
Now he can ask the app himself — and get a real, data-backed answer in plain English. 🚀

---
*Built with Databricks Free Edition · NASA APIs · Genie Agent · Gradio*
