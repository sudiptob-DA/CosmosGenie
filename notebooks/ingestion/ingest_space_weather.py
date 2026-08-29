# Databricks notebook source
# MAGIC %md
# MAGIC # ingest_space_weather — NASA DONKI

# COMMAND ----------

import requests
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime, timedelta

NASA_KEY   = dbutils.secrets.get(scope="cosmos", key="nasa_api_key")
end_date   = datetime.now()
start_date = end_date - timedelta(days=30)
fmt        = "%Y-%m-%d"
records    = []

# Solar Flares
flares = requests.get(
    f"https://api.nasa.gov/DONKI/FLR?startDate={start_date:{fmt}}&endDate={end_date:{fmt}}&api_key={NASA_KEY}",
    timeout=30
).json() or []

for f in flares:
    records.append({
        "event_id": f.get("flrID",""), "event_type": "FLR",
        "begin_time": f.get("beginTime"), "peak_time": f.get("peakTime"),
        "end_time": f.get("endTime"), "class_type": f.get("classType",""),
        "active_region": f.get("activeRegionNum"), "kp_index": None,
        "fetched_at": datetime.now().isoformat()
    })

# Geomagnetic Storms
storms = requests.get(
    f"https://api.nasa.gov/DONKI/GST?startDate={start_date:{fmt}}&endDate={end_date:{fmt}}&api_key={NASA_KEY}",
    timeout=30
).json() or []

for s in storms:
    kp = max((k.get("kpIndex",0) for k in s.get("allKpIndex",[])), default=None)
    records.append({
        "event_id": s.get("gstID",""), "event_type": "GST",
        "begin_time": s.get("startTime"), "peak_time": None, "end_time": None,
        "class_type": f"G{int(kp//3) if kp else 1}", "active_region": None,
        "kp_index": kp, "fetched_at": datetime.now().isoformat()
    })

schema = StructType([
    StructField("event_id",    StringType()), StructField("event_type",  StringType()),
    StructField("begin_time",  StringType()), StructField("peak_time",   StringType()),
    StructField("end_time",    StringType()), StructField("class_type",  StringType()),
    StructField("active_region",IntegerType()),StructField("kp_index",   DoubleType()),
    StructField("fetched_at",  StringType()),
])

def to_ts(col): return F.to_timestamp(col, "yyyy-MM-dd'T'HH:mm'Z'")
df = (spark.createDataFrame(records, schema)
      .withColumn("begin_time", to_ts("begin_time"))
      .withColumn("peak_time",  to_ts("peak_time"))
      .withColumn("end_time",   to_ts("end_time"))
      .withColumn("fetched_at", F.to_timestamp("fetched_at")))

df.createOrReplaceTempView("new_events")
spark.sql("""
  MERGE INTO cosmos.space.space_weather_events t
  USING new_events s ON t.event_id = s.event_id
  WHEN NOT MATCHED THEN INSERT *
""")
print(f"Loaded {len(records)} space weather events")

