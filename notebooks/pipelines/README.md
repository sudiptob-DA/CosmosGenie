# CosmosGenie — Lakeflow Spark Declarative Pipeline

Bronze → Silver ingestion pipeline for NASA asteroid and space weather data.

## Structure

```
bronze/
  neo_close_approaches.py   — Raw NASA NeoWs API pull (last 7 days)
  space_weather_events.py   — Raw NASA DONKI FLR + GST (last 30 days)
silver/
  neo_close_approaches.py   — Cleaned + typed + DQ expectations
  space_weather_events.py   — Cleaned + typed + DQ expectations
```

## Data Quality Expectations (visible in pipeline UI)

| Table | Expectation | Constraint |
|---|---|---|
| neo_close_approaches | valid_distance | miss_distance_au > 0 |
| neo_close_approaches | valid_approach_date | approach_date IS NOT NULL |
| space_weather_events | valid_event_type | event_type IN ('FLR', 'GST') |
| space_weather_events | valid_begin_time | begin_time IS NOT NULL |

## Pipeline Settings

- Catalog: `cosmos` / Schema: `space`
- Mode: Triggered (scheduled daily at 06:00 UTC via Lakeflow Job)
- Serverless: true
- NASA API key: stored as Databricks secret `{{secrets/cosmos/nasa_api_key}}`

## Setup on Free Edition

1. Create the secret scope: `databricks secrets create-scope cosmos`
2. Store your NASA key: `databricks secrets put-secret cosmos nasa_api_key --string-value YOUR_KEY`
3. Create a new SDP pipeline, set catalog=cosmos schema=space
4. Point libraries at this folder
5. Run — tables land in `cosmos.space.neo_close_approaches` and `cosmos.space.space_weather_events`
