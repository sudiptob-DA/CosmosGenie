# Databricks notebook source
# MAGIC %md
# MAGIC # ingest_moon_phases — USNO API

# COMMAND ----------

import requests
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime

current_year = datetime.now().year
records      = []

for year in [current_year, current_year + 1]:
    resp = requests.get(
        f"https://aa.usno.navy.mil/api/moon/phases/year?year={year}&nump=50",
        timeout=15
    ).json()
    for p in resp.get("phasedata", []):
        phase_dt = datetime.strptime(p["date"].strip(), "%Y %b %d")
        records.append({
            "phase_date":   phase_dt.strftime("%Y-%m-%d"),
            "phase_time":   p.get("time", ""),
            "phase_name":   p.get("phase", ""),
            "year":         year,
            "is_supermoon": False,
            "fetched_at":   datetime.now().isoformat()
        })

schema = StructType([
    StructField("phase_date",   StringType()), StructField("phase_time",  StringType()),
    StructField("phase_name",   StringType()), StructField("year",        IntegerType()),
    StructField("is_supermoon", BooleanType()),StructField("fetched_at",  StringType()),
])

df = (spark.createDataFrame(records, schema)
      .withColumn("phase_date", F.to_date("phase_date"))
      .withColumn("fetched_at", F.to_timestamp("fetched_at")))

df.createOrReplaceTempView("new_phases")
spark.sql("""
  MERGE INTO cosmos.space.moon_phases t
  USING new_phases s ON t.phase_date = s.phase_date AND t.phase_name = s.phase_name
  WHEN NOT MATCHED THEN INSERT *
""")
print(f"Loaded {len(records)} moon phase records")

