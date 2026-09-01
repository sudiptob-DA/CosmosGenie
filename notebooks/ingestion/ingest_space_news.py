# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # ingest_space_news — Spaceflight News API

# COMMAND ----------

import requests
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime

data    = requests.get("https://api.spaceflightnewsapi.net/v4/articles/?limit=50&ordering=-published_at", timeout=30).json()
records = []

for a in data.get("results", []):
    records.append({
        "article_id":   str(a.get("id","")),
        "title":        (a.get("title","") or "")[:500],
        "summary":      (a.get("summary","") or "")[:2000],
        "url":          a.get("url",""),
        "image_url":    a.get("image_url",""),
        "news_site":    a.get("news_site",""),
        "published_at": a.get("published_at"),
        "is_featured":  a.get("featured", False),
        "fetched_at":   datetime.now().isoformat()
    })

schema = StructType([
    StructField("article_id",   StringType()), StructField("title",        StringType()),
    StructField("summary",      StringType()), StructField("url",          StringType()),
    StructField("image_url",    StringType()), StructField("news_site",    StringType()),
    StructField("published_at", StringType()), StructField("is_featured",  BooleanType()),
    StructField("fetched_at",   StringType()),
])

df = (spark.createDataFrame(records, schema)
      .withColumn("published_at", F.to_timestamp("published_at"))
      .withColumn("fetched_at",   F.to_timestamp("fetched_at")))

df.createOrReplaceTempView("new_news")
spark.sql("""
  MERGE INTO cosmos.space.space_news t
  USING new_news s ON t.article_id = s.article_id
  WHEN MATCHED THEN UPDATE SET *
  WHEN NOT MATCHED THEN INSERT *
""")
print(f"Upserted {len(records)} news articles")
