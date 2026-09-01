"""Curated planetary events — conjunctions, oppositions, meteor showers, eclipses.

SOURCE DATA:
  Meteor showers: International Meteor Organization (IMO) — stable annual dates
  Oppositions:    Astronomical almanac / synodic-period computed
  Conjunctions:   Astronomical almanac + ephemeris (dates ±1-2 days)
  Eclipses:       NASA Five Millennium Canon (Espenak & Meeus) — dates in UT
                  eclipse.gsfc.nasa.gov  |  science.nasa.gov/eclipses

  For exact conjunction dates, verify at: ssd.jpl.nasa.gov/horizons
"""

# Databricks notebook source
# MAGIC %md
# MAGIC # load_planetary_events — One-time Static Load
# MAGIC Meteor showers from IMO. Oppositions from synodic periods.
# MAGIC Conjunctions from ephemeris data (±1-2 days). Eclipses from NASA (UT dates).

# COMMAND ----------

from pyspark.sql import functions as F

# (date, type, primary_body, secondary_body, angular_sep_deg, visibility, description)
events = [
    # ─── 2025 ─────────────────────────────────────────────────────
    ("2025-01-16","Opposition","Mars",None,None,"All night",
     "Mars at opposition — closest to Earth, largest and brightest all night"),
    ("2025-03-14","Eclipse","Moon",None,None,"Americas, W Europe, W Africa",
     "Total lunar eclipse — greatest eclipse 06:59 UT (NASA, Saros 123)"),
    ("2025-03-29","Eclipse","Sun",None,None,"NW Africa, Europe, NE N.America",
     "Partial solar eclipse (NASA)"),
    ("2025-08-12","Meteor Shower","Perseids",None,None,"All night",
     "Perseid meteor shower peak — up to 100 meteors/hour (IMO)"),
    ("2025-09-07","Eclipse","Moon",None,None,"Asia, Australia, E Africa, Europe",
     "Total lunar eclipse — deep totality visible across the Eastern Hemisphere (NASA)"),
    ("2025-09-21","Opposition","Saturn",None,None,"All night",
     "Saturn at opposition — rings visible all night"),
    ("2025-09-21","Eclipse","Sun",None,None,"S Pacific, New Zealand, Antarctica",
     "Partial solar eclipse (NASA)"),
    ("2025-11-17","Meteor Shower","Leonids",None,None,"After midnight",
     "Leonid meteor shower peak — up to 15 meteors/hour"),
    ("2025-12-14","Meteor Shower","Geminids",None,None,"All night",
     "Geminid meteor shower peak — up to 120 meteors/hour, best shower of the year"),

    # ─── 2026 ─────────────────────────────────────────────────────
    ("2026-01-04","Meteor Shower","Quadrantids",None,None,"Pre-dawn",
     "Quadrantid meteor shower peak — up to 80 meteors/hour, short peak"),
    ("2026-01-08","Conjunction","Venus","Mars","0.03","Pre-dawn",
     "Venus and Mars in very close conjunction in Capricorn (morning sky)"),
    ("2026-01-10","Opposition","Jupiter",None,None,"All night",
     "Jupiter at opposition — largest and brightest of the year, visible all night"),
    ("2026-02-17","Eclipse","Sun",None,None,"Antarctica, S tip of S.America",
     "Annular solar eclipse (NASA)"),
    ("2026-03-03","Eclipse","Moon",None,None,"Pacific, Americas, E Asia, Australia",
     "Total lunar eclipse — greatest eclipse ~11:33 UT (NASA)"),
    ("2026-03-08","Conjunction","Venus","Saturn","1.0","Evening",
     "Venus and Saturn appear ~1 degree apart in western evening twilight"),
    ("2026-04-22","Meteor Shower","Lyrids",None,None,"After midnight",
     "Lyrid meteor shower peak — up to 20 meteors/hour"),
    ("2026-08-12","Meteor Shower","Perseids",None,None,"All night",
     "Perseid meteor shower peak — up to 100 meteors/hour"),
    ("2026-08-12","Eclipse","Sun",None,None,"Greenland, Iceland, Spain",
     "Total solar eclipse — path crosses Greenland, Iceland, N Russia and Spain (NASA)"),
    ("2026-08-28","Eclipse","Moon",None,None,"Americas, Europe, Africa",
     "Partial lunar eclipse (NASA)"),
    ("2026-09-26","Opposition","Neptune",None,None,"All night (telescope)",
     "Neptune at opposition — mag ~7.8, requires binoculars/telescope"),
    ("2026-10-04","Opposition","Saturn",None,None,"All night",
     "Saturn at opposition — rings well placed, visible all night"),
    ("2026-11-17","Meteor Shower","Leonids",None,None,"After midnight",
     "Leonid meteor shower peak — up to 15 meteors/hour"),
    ("2026-12-14","Meteor Shower","Geminids",None,None,"All night",
     "Geminid meteor shower peak — best meteor shower of 2026, up to 120/hour"),

    # ─── 2027 ─────────────────────────────────────────────────────
    ("2027-01-04","Meteor Shower","Quadrantids",None,None,"Pre-dawn",
     "Quadrantid meteor shower peak — up to 80 meteors/hour"),
    ("2027-02-06","Eclipse","Sun",None,None,"S.America, Atlantic, W Africa",
     "Annular solar eclipse — central duration up to 7m51s (NASA, Saros 131)"),
    ("2027-02-19","Opposition","Mars",None,None,"All night",
     "Mars at opposition — closest approach to Earth, visible all night"),
    ("2027-02-20","Eclipse","Moon",None,None,"Americas, Europe, Africa",
     "Penumbral lunar eclipse — subtle shading only (NASA)"),
    ("2027-04-22","Meteor Shower","Lyrids",None,None,"After midnight",
     "Lyrid meteor shower peak — up to 20 meteors/hour"),
    ("2027-08-02","Eclipse","Sun",None,None,"S Spain, N Africa, Middle East",
     "Total solar eclipse — up to 6m23s totality, one of the longest for decades (NASA)"),
    ("2027-08-12","Meteor Shower","Perseids",None,None,"All night",
     "Perseid meteor shower peak — up to 100 meteors/hour"),
    ("2027-08-17","Eclipse","Moon",None,None,"Africa, Asia, Australia",
     "Penumbral lunar eclipse — subtle shading only (NASA)"),
    ("2027-11-17","Meteor Shower","Leonids",None,None,"After midnight",
     "Leonid meteor shower peak — up to 15 meteors/hour"),
    ("2027-11-25","Conjunction","Venus","Mars","0.5","Evening",
     "Venus and Mars in close conjunction in Sagittarius (evening sky)"),
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
