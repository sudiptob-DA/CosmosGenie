"""Curated planetary events — conjunctions, oppositions, meteor showers.

SOURCE DATA:
  Meteor showers: International Meteor Organization (IMO) — stable annual dates
  Oppositions: Computed from synodic periods (predictable orbital mechanics)
  Conjunctions: Astronomical almanac data — dates approximate ±1-3 days
  
  For exact conjunction dates, verify at: ssd.jpl.nasa.gov/horizons
"""

# Databricks notebook source
# MAGIC %md
# MAGIC # load_planetary_events — One-time Static Load
# MAGIC Meteor shower dates from IMO. Opposition dates from synodic periods.
# MAGIC Conjunction dates from astronomical almanacs (±1-3 days).

# COMMAND ----------

from pyspark.sql import functions as F

# (date, type, primary_body, secondary_body, angular_sep_deg, visibility, description)
events = [
    # ─── 2025 ─────────────────────────────────────────────────────
    ("2025-01-16","Opposition","Mars",None,None,"All night",
     "Mars at opposition — closest to Earth, largest and brightest all night"),
    ("2025-08-12","Meteor Shower","Perseids",None,None,"All night",
     "Perseid meteor shower peak — up to 100 meteors/hour (IMO)"),
    ("2025-09-21","Opposition","Saturn",None,None,"All night",
     "Saturn at opposition — rings visible all night"),
    ("2025-11-17","Meteor Shower","Leonids",None,None,"After midnight",
     "Leonid meteor shower peak — up to 15 meteors/hour"),
    ("2025-12-14","Meteor Shower","Geminids",None,None,"All night",
     "Geminid meteor shower peak — up to 120 meteors/hour, best shower of the year"),

    # ─── 2026 ─────────────────────────────────────────────────────
    ("2026-01-04","Meteor Shower","Quadrantids",None,None,"Pre-dawn",
     "Quadrantid meteor shower peak — up to 80 meteors/hour, short peak"),
    ("2026-02-01","Conjunction","Venus","Saturn","1.0","Evening",
     "Venus and Saturn appear ~1 degree apart in evening sky"),
    ("2026-04-22","Meteor Shower","Lyrids",None,None,"After midnight",
     "Lyrid meteor shower peak — up to 20 meteors/hour"),
    ("2026-08-12","Meteor Shower","Perseids",None,None,"All night",
     "Perseid meteor shower peak — up to 100 meteors/hour"),
    ("2026-09-21","Opposition","Jupiter",None,None,"All night",
     "Jupiter at opposition — largest and brightest, visible all night"),
    ("2026-11-17","Meteor Shower","Leonids",None,None,"After midnight",
     "Leonid meteor shower peak — up to 15 meteors/hour"),
    ("2026-12-14","Meteor Shower","Geminids",None,None,"All night",
     "Geminid meteor shower peak — best meteor shower of 2026, up to 120/hour"),

    # ─── 2027 ─────────────────────────────────────────────────────
    ("2027-01-04","Meteor Shower","Quadrantids",None,None,"Pre-dawn",
     "Quadrantid meteor shower peak — up to 80 meteors/hour"),
    ("2027-02-19","Opposition","Mars",None,None,"All night",
     "Mars at opposition — closest approach to Earth, visible all night"),
    ("2027-04-22","Meteor Shower","Lyrids",None,None,"After midnight",
     "Lyrid meteor shower peak — up to 20 meteors/hour"),
    ("2027-08-12","Meteor Shower","Perseids",None,None,"All night",
     "Perseid meteor shower peak — up to 100 meteors/hour"),
    ("2027-10-07","Conjunction","Venus","Mars","0.5","Evening",
     "Venus and Mars appear ~0.5 degrees apart in evening sky"),
    ("2027-11-17","Meteor Shower","Leonids",None,None,"After midnight",
     "Leonid meteor shower peak — up to 15 meteors/hour"),
    ("2027-12-14","Meteor Shower","Geminids",None,None,"All night",
     "Geminid meteor shower peak — up to 120 meteors/hour"),
]

cols = ["event_date","event_type","primary_body","secondary_body",
        "angular_separation_deg","visibility","description"]
df = spark.createDataFrame(events, cols)
df = (df.withColumn("event_date", F.to_date("event_date"))
        .withColumn("angular_separation_deg", F.col("angular_separation_deg").cast("double"))
        .withColumn("year", F.year("event_date")))

df.write.format("delta").mode("overwrite").saveAsTable("cosmos.space.planetary_events")
print(f"Loaded {df.count()} planetary events")
