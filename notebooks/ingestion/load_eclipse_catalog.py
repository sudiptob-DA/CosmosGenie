# Databricks notebook source
# MAGIC %md
# MAGIC # load_eclipse_catalog — One-time Static Load

# COMMAND ----------

from pyspark.sql import functions as F

eclipses = [
  ("2026-08-12","Partial","Solar",  0.0,"N Europe, Greenland, N Africa",           0.965,0.896),
  ("2027-08-02","Total",  "Solar",  6.4,"Morocco, Algeria, Tunisia, Egypt, Saudi", 0.076,1.079),
  ("2028-07-22","Total",  "Solar",  5.2,"Australia, New Zealand, S Pacific",        0.174,1.056),
  ("2030-11-25","Total",  "Solar",  3.7,"S Africa, Indian Ocean, Australia",        0.351,1.047),
  ("2034-03-20","Total",  "Solar",  4.1,"Nigeria, Sudan, Ethiopia, Saudi, India",   0.063,1.065),
  ("2025-09-07","Total",  "Lunar",  3.6,"Europe, Africa, Asia, Australia",         -0.219,1.368),
  ("2026-03-03","Total",  "Lunar",  1.3,"Americas, Europe, W Africa",              -0.388,1.153),
  ("2026-08-28","Partial","Lunar",  0.0,"Americas, Europe, Africa",                -0.900,0.930),
  ("2028-12-31","Total",  "Lunar",  5.1,"Americas, Europe, Africa, Asia",          -0.098,1.244),
  ("2029-06-26","Total",  "Lunar",  1.7,"Global",                                  -0.133,1.844),
]

cols = ["eclipse_date","eclipse_type","body","duration_minutes","path_description","gamma","magnitude"]
df = spark.createDataFrame(eclipses, cols)
df = (df.withColumn("eclipse_date", F.to_date("eclipse_date"))
        .withColumn("year", F.year("eclipse_date")))

df.write.format("delta").mode("overwrite").saveAsTable("cosmos.space.eclipse_catalog")
print(f"Loaded {df.count()} eclipse records")

