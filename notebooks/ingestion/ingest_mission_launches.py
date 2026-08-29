# Databricks notebook source
# MAGIC %md
# MAGIC # ingest_mission_launches — The Space Devs

# COMMAND ----------

import requests
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime

def safe(d, *keys, default=""):
    for k in keys:
        if not isinstance(d, dict): return default
        d = d.get(k) or {}
    return d if d else default

data    = requests.get("https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=25&format=json", timeout=30).json()
records = []

for L in data.get("results", []):
    mission = L.get("mission") or {}
    desc    = (mission.get("description","") or "").lower()
    mtype   = (mission.get("type","") or "").lower()
    records.append({
        "launch_id":           L.get("id",""),
        "name":                L.get("name",""),
        "launch_date":         L.get("net"),
        "status":              safe(L,"status","name"),
        "agency":              safe(L,"launch_service_provider","name"),
        "agency_country":      safe(L,"launch_service_provider","country_code"),
        "rocket":              safe(L,"rocket","configuration","name"),
        "mission_name":        mission.get("name",""),
        "mission_description": (mission.get("description","") or "")[:1000],
        "mission_type":        mission.get("type",""),
        "launch_site":         safe(L,"pad","name"),
        "launch_site_country": safe(L,"pad","location","country_code"),
        "is_crewed":           mtype in ("human exploration","crewed"),
        "is_moon_mission":     any(w in desc for w in ["moon","lunar","artemis","diana","luna"]),
        "webcast_url":         ((L.get("vidURLs") or [{}])[0] or {}).get("url",""),
        "fetched_at":          datetime.now().isoformat()
    })

schema = StructType([
    StructField("launch_id",           StringType()), StructField("name",                StringType()),
    StructField("launch_date",         StringType()), StructField("status",              StringType()),
    StructField("agency",              StringType()), StructField("agency_country",      StringType()),
    StructField("rocket",              StringType()), StructField("mission_name",        StringType()),
    StructField("mission_description", StringType()), StructField("mission_type",        StringType()),
    StructField("launch_site",         StringType()), StructField("launch_site_country", StringType()),
    StructField("is_crewed",           BooleanType()),StructField("is_moon_mission",     BooleanType()),
    StructField("webcast_url",         StringType()), StructField("fetched_at",          StringType()),
])

df = (spark.createDataFrame(records, schema)
      .withColumn("launch_date", F.to_timestamp("launch_date"))
      .withColumn("fetched_at",  F.to_timestamp("fetched_at")))

df.createOrReplaceTempView("new_launches")
spark.sql("""
  MERGE INTO cosmos.space.mission_launches t
  USING new_launches s ON t.launch_id = s.launch_id
  WHEN MATCHED THEN UPDATE SET *
  WHEN NOT MATCHED THEN INSERT *
""")
print(f"Upserted {len(records)} launches")

