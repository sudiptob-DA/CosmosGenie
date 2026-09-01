"""Bronze: NASA DONKI - Space Weather Events (raw API pull)."""

import requests
from datetime import datetime, timedelta
from pyspark import pipelines as dp
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType,
)


_WEATHER_SCHEMA = StructType([
    StructField("event_id", StringType()),
    StructField("event_type", StringType()),
    StructField("begin_time", StringType()),
    StructField("peak_time", StringType()),
    StructField("end_time", StringType()),
    StructField("class_type", StringType()),
    StructField("active_region", IntegerType()),
    StructField("kp_index", DoubleType()),
    StructField("fetched_at", StringType()),
])


def _fetch_donki(api_key: str) -> list:
    """Fetch Solar Flares (FLR) and Geomagnetic Storms (GST) from NASA DONKI."""
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=30)
    fmt = "%Y-%m-%d"
    records = []

    # Solar Flares
    flr_url = (
        f"https://api.nasa.gov/DONKI/FLR"
        f"?startDate={start_dt:{fmt}}&endDate={end_dt:{fmt}}"
        f"&api_key={api_key}"
    )
    flr_resp = requests.get(flr_url, timeout=30)
    flr_resp.raise_for_status()
    flares = flr_resp.json() if flr_resp.text.strip() else []
    for flr in flares:
        records.append({
            "event_id": flr.get("flrID", ""),
            "event_type": "FLR",
            "begin_time": flr.get("beginTime"),
            "peak_time": flr.get("peakTime"),
            "end_time": flr.get("endTime"),
            "class_type": flr.get("classType", ""),
            "active_region": flr.get("activeRegionNum"),
            "kp_index": None,
            "fetched_at": end_dt.isoformat(),
        })

    # Geomagnetic Storms
    gst_url = (
        f"https://api.nasa.gov/DONKI/GST"
        f"?startDate={start_dt:{fmt}}&endDate={end_dt:{fmt}}"
        f"&api_key={api_key}"
    )
    gst_resp = requests.get(gst_url, timeout=30)
    gst_resp.raise_for_status()
    storms = gst_resp.json() if gst_resp.text.strip() else []
    for gst in storms:
        kp_vals = [k.get("kpIndex", 0) for k in gst.get("allKpIndex", [])]
        kp = max(kp_vals) if kp_vals else None
        g_scale = f"G{int(kp // 3)}" if kp else "G1"
        records.append({
            "event_id": gst.get("gstID", ""),
            "event_type": "GST",
            "begin_time": gst.get("startTime"),
            "peak_time": None,
            "end_time": None,
            "class_type": g_scale,
            "active_region": None,
            "kp_index": kp,
            "fetched_at": end_dt.isoformat(),
        })

    return records


@dp.materialized_view(
    comment="Raw NASA DONKI space weather events (FLR + GST) - last 30 days",
)
def bronze_space_weather_events():
    api_key = spark.conf.get("nasa_api_key")
    rows = _fetch_donki(api_key)
    return spark.createDataFrame(rows, schema=_WEATHER_SCHEMA)
