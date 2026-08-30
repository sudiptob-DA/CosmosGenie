# pipelines/

Lakeflow Spark Declarative Pipeline source files — full bronze → silver → gold medallion.

For pipeline setup, scheduling, and Genie Space configuration see the
[main README](../../README.md#step-5--create-the-lakeflow-sdp-pipeline).

## Files

| Folder | Table produced | Description |
|---|---|---|
| `bronze/neo_close_approaches.py` | `bronze_neo_close_approaches` | Raw NASA NeoWs API pull |
| `bronze/space_weather_events.py` | `bronze_space_weather_events` | Raw NASA DONKI API pull |
| `silver/neo_close_approaches.py` | `neo_close_approaches` | Cleaned + typed + 2 DQ expectations |
| `silver/space_weather_events.py` | `space_weather_events` | Cleaned + typed + 2 DQ expectations |
| `gold/asteroid_alerts.py` | `gold_asteroid_alerts` | threat_level, miss_distance_lunar, size_estimate |
| `gold/space_weather_active.py` | `gold_space_weather_active` | severity rating, aurora_likelihood |
| `gold/upcoming_events.py` | `gold_upcoming_events` | Unified eclipses + planetary + launches timeline |
| `gold/cosmic_kpis.py` | `gold_cosmic_kpis` | Single-row KPI bar summary |
