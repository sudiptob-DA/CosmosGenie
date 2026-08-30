# CosmosGenie — Lakeflow Spark Declarative Pipeline

Full **bronze → silver → gold** medallion architecture.

## Pipeline DAG

```
NASA NeoWs API ──→ bronze_neo_close_approaches ──→ neo_close_approaches ──→ gold_asteroid_alerts ─┐
                                                                                                   ├─→ gold_upcoming_events
NASA DONKI API ──→ bronze_space_weather_events ──→ space_weather_events ──→ gold_space_weather_active│
                                                                                                   │
eclipse_catalog (static) ──────────────────────────────────────────────────────────────────────────┤
planetary_events (static) ─────────────────────────────────────────────────────────────────────────┤
mission_launches (API) ────────────────────────────────────────────────────────────────────────────┘
                                                                                                   
neo_close_approaches + eclipse_catalog + planetary_events + moon_phases + space_weather_events
    └──→ gold_cosmic_kpis (single-row KPI summary)
```

## Layer Details

### Bronze (Raw API Pull)
| File | Table | Source |
|---|---|---|
| `bronze/neo_close_approaches.py` | `bronze_neo_close_approaches` | NASA NeoWs — last 7 days of asteroid approaches |
| `bronze/space_weather_events.py` | `bronze_space_weather_events` | NASA DONKI — solar flares (FLR) + geomagnetic storms (GST) |

### Silver (Cleaned + Typed + DQ Expectations)
| File | Table | Expectations |
|---|---|---|
| `silver/neo_close_approaches.py` | `neo_close_approaches` | `valid_distance` (miss_distance_au > 0), `valid_approach_date` (NOT NULL) |
| `silver/space_weather_events.py` | `space_weather_events` | `valid_event_type` (IN FLR/GST), `valid_begin_time` (NOT NULL) |

### Gold (Analytics-Ready, Business Logic)
| File | Table | Purpose |
|---|---|---|
| `gold/asteroid_alerts.py` | `gold_asteroid_alerts` | Next 30 days, threat_level (HIGH/WATCH/SAFE), lunar distances |
| `gold/space_weather_active.py` | `gold_space_weather_active` | Significant events, severity rating, aurora likelihood |
| `gold/upcoming_events.py` | `gold_upcoming_events` | Unified 12-month timeline: eclipses + planetary + launches |
| `gold/cosmic_kpis.py` | `gold_cosmic_kpis` | Single-row KPI bar: asteroids this week, days to eclipse, etc. |

## Configuration

| Key | Value | Description |
|---|---|---|
| `nasa_api_key` | `{{secrets/cosmos/nasa_api_key}}` | NASA API key for NeoWs + DONKI endpoints |

## Setup

```
Target catalog: cosmos
Target schema:  space
Compute:        Serverless
Mode:           Triggered
```
