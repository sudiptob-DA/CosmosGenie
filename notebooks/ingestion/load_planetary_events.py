# Databricks notebook source
# MAGIC %md
# MAGIC # load_planetary_events — One-time Static Load

# COMMAND ----------

from pyspark.sql import functions as F

events = [
  ("2026-01-18","Conjunction","Venus","Saturn","0.5","Evening","Venus and Saturn appear 0.5 degrees apart"),
  ("2026-05-13","Opposition","Mars",None,None,"All night","Mars at opposition — largest and brightest"),
  ("2026-08-12","Meteor Shower","Perseids",None,None,"All night","Perseid peak — up to 100 meteors/hr"),
  ("2026-09-08","Alignment","5 Planets",None,None,"Pre-dawn","5-planet parade visible before sunrise"),
  ("2026-10-29","Conjunction","Jupiter","Mars","0.3","Evening","Jupiter and Mars within 0.3 degrees"),
  ("2026-11-17","Meteor Shower","Leonids",None,None,"After midnight","Leonid peak — up to 15 meteors/hr"),
  ("2026-12-14","Meteor Shower","Geminids",None,None,"All night","Geminid peak — best of the year, ~120/hr"),
  ("2027-01-18","Conjunction","Venus","Saturn","0.5","Evening","Venus passes Saturn"),
  ("2027-02-19","Opposition","Mars",None,None,"All night","Mars opposition — closest approach"),
  ("2027-08-12","Meteor Shower","Perseids",None,None,"All night","Perseid peak 2027"),
]

cols = ["event_date","event_type","primary_body","secondary_body",
        "angular_separation_deg","visibility","description"]
df = spark.createDataFrame(events, cols)
df = (df.withColumn("event_date", F.to_date("event_date"))
        .withColumn("angular_separation_deg", F.col("angular_separation_deg").cast("double"))
        .withColumn("year", F.year("event_date")))

df.write.format("delta").mode("overwrite").saveAsTable("cosmos.space.planetary_events")
print(f"Loaded {df.count()} planetary events")

