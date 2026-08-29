"""Bronze: NASA NeoWs - Asteroid Close Approaches (raw API pull)."""

import requests
from datetime import datetime, timedelta
from pyspark import pipelines as dp
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, BooleanType,
)


_NEOWS_SCHEMA = StructType([
    StructField("asteroid_id", StringType()),
    StructField("name", StringType()),
    StructField("approach_date", StringType()),
    StructField("miss_distance_au", DoubleType()),
    StructField("miss_distance_km", DoubleType()),
    StructField("velocity_kps", DoubleType()),
    StructField("diameter_min_m", DoubleType()),
    StructField("diameter_max_m", DoubleType()),
    StructField("is_potentially_hazardous", BooleanType()),
    StructField("absolute_magnitude", DoubleType()),
    StructField("fetched_at", StringType()),
])


def _fetch_neows(api_key: str) -> list:
    """Call NASA NeoWs for the last 7 days and flatten the response."""
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=7)
    url = (
        "https://api.nasa.gov/neo/rest/v1/feed"
        f"?start_date={start_dt:%Y-%m-%d}"
        f"&end_date={end_dt:%Y-%m-%d}"
        f"&api_key={api_key}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    records = []
    for date_str, asteroids in data.get("near_earth_objects", {}).items():
        for a in asteroids:
            ca = a["close_approach_data"][0] if a.get("close_approach_data") else {}
            miss = ca.get("miss_distance", {})
            vel = ca.get("relative_velocity", {})
            diam = a.get("estimated_diameter", {}).get("meters", {})
            records.append({
                "asteroid_id": a.get("id", ""),
                "name": a.get("name", ""),
                "approach_date": ca.get("close_approach_date"),
                "miss_distance_au": float(miss.get("astronomical", 0) or 0),
                "miss_distance_km": float(miss.get("kilometers", 0) or 0),
                "velocity_kps": float(vel.get("kilometers_per_second", 0) or 0),
                "diameter_min_m": float(diam.get("estimated_diameter_min", 0) or 0),
                "diameter_max_m": float(diam.get("estimated_diameter_max", 0) or 0),
                "is_potentially_hazardous": a.get(
                    "is_potentially_hazardous_asteroid", False
                ),
                "absolute_magnitude": float(
                    a.get("absolute_magnitude_h", 0) or 0
                ),
                "fetched_at": end_dt.isoformat(),
            })
    return records


@dp.materialized_view(
    comment="Raw NASA NeoWs asteroid close-approach records - last 7 days",
)
def bronze_neo_close_approaches():
    api_key = spark.conf.get("nasa_api_key")
    rows = _fetch_neows(api_key)
    return spark.createDataFrame(rows, schema=_NEOWS_SCHEMA)
