# Databricks notebook source
# MAGIC %md
# MAGIC # ingest_asteroids — NASA NeoWs

# COMMAND ----------

import requests
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime, timedelta

NASA_KEY = dbutils.secrets.get(scope="cosmos", key="nasa_api_key")
# For testing without secrets: NASA_KEY = "DEMO_KEY"

end_date   = datetime.now()
start_date = end_date - timedelta(days=7)

url = (f"https://api.nasa.gov/neo/rest/v1/feed"
       f"?start_date={start_date:%Y-%m-%d}"
       f"&end_date={end_date:%Y-%m-%d}"
       f"&api_key={NASA_KEY}")

resp = requests.get(url, timeout=30)
data = resp.json()

records = []
for date_str, asteroids in data.get("near_earth_objects", {}).items():
    for a in asteroids:
        ca = a["close_approach_data"][0] if a["close_approach_data"] else {}
        records.append({
            "asteroid_id":             a["id"],
            "name":                    a["name"],
            "approach_date":           ca.get("close_approach_date"),
            "miss_distance_au":        float(ca.get("miss_distance", {}).get("astronomical", 0) or 0),
            "miss_distance_km":        float(ca.get("miss_distance", {}).get("kilometers",    0) or 0),
            "velocity_kps":            float(ca.get("relative_velocity", {}).get("kilometers_per_second", 0) or 0),
            "diameter_min_m":          a.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_min", 0),
            "diameter_max_m":          a.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max", 0),
            "is_potentially_hazardous":a.get("is_potentially_hazardous_asteroid", False),
            "absolute_magnitude":      a.get("absolute_magnitude_h", 0),
            "fetched_at":              datetime.now().isoformat()
        })

schema = StructType([
    StructField("asteroid_id",            StringType()),
    StructField("name",                   StringType()),
    StructField("approach_date",          StringType()),
    StructField("miss_distance_au",       DoubleType()),
    StructField("miss_distance_km",       DoubleType()),
    StructField("velocity_kps",           DoubleType()),
    StructField("diameter_min_m",         DoubleType()),
    StructField("diameter_max_m",         DoubleType()),
    StructField("is_potentially_hazardous", BooleanType()),
    StructField("absolute_magnitude",     DoubleType()),
    StructField("fetched_at",             StringType()),
])

df = (spark.createDataFrame(records, schema)
      .withColumn("approach_date", F.to_date("approach_date"))
      .withColumn("fetched_at",    F.to_timestamp("fetched_at")))

df.createOrReplaceTempView("new_asteroids")
spark.sql("""
  MERGE INTO cosmos.space.neo_close_approaches t
  USING new_asteroids s
  ON t.asteroid_id = s.asteroid_id AND t.approach_date = s.approach_date
  WHEN NOT MATCHED THEN INSERT *
""")
print(f"Loaded {len(records)} asteroid records")

