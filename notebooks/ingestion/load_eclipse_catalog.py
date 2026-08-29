"""Bronze: NASA 5-Millennium Eclipse Catalog - One-time Static Load.

SOURCE DATA: NASA Goddard Space Flight Center
  Solar: eclipse.gsfc.nasa.gov/SEcat5/SE2001-2100.html
  Lunar: eclipse.gsfc.nasa.gov/LEcat5/LE2001-2100.html
All dates, types, durations, gamma, and magnitude values are
copied directly from NASA's Five Millennium Catalog.
"""

# Databricks notebook source
# MAGIC %md
# MAGIC # load_eclipse_catalog — One-time Static Load
# MAGIC Data sourced from **NASA Five Millennium Eclipse Catalog** (GSFC).

# COMMAND ----------

from pyspark.sql import functions as F

# (date, type, body, duration_min, path_description, gamma, magnitude)
# Solar: duration = central duration in minutes
# Lunar: duration = total phase duration in minutes
eclipses = [
    # ─── SOLAR ECLIPSES (Total + Annular + Hybrid, 2025-2034) ───
    # Source: eclipse.gsfc.nasa.gov/SEcat5/SE2001-2100.html
    ("2026-02-17","Annular","Solar",  2.3,"S South America, Antarctica, W & S Africa",          -0.9743, 0.9630),
    ("2026-08-12","Total",  "Solar",  2.3,"Arctic, Greenland, Iceland, Atlantic, N Spain",       0.8977, 1.0386),
    ("2027-02-06","Annular","Solar",  7.8,"S Pacific, Argentina, Chile, Uruguay, Atlantic, Africa", -0.2952, 0.9281),
    ("2027-08-02","Total",  "Solar",  6.4,"Morocco, Algeria, Tunisia, Libya, Egypt, Saudi Arabia", 0.1421, 1.0790),
    ("2028-01-26","Annular","Solar", 10.4,"E Pacific, Ecuador, Peru, Brazil, Suriname, Atlantic", 0.3901, 0.9208),
    ("2028-07-22","Total",  "Solar",  5.2,"Australia (Sydney), New Zealand, S Pacific",         -0.6056, 1.0560),
    ("2030-06-01","Annular","Solar",  5.3,"N Africa, Greece, Turkey, Russia, N China, Japan",    0.5626, 0.9443),
    ("2030-11-25","Total",  "Solar",  3.7,"S Africa, S Indian Ocean, Australia",                -0.3867, 1.0468),
    ("2031-05-21","Annular","Solar",  5.4,"S Africa, S Indian Ocean, E Indies, Australia",      -0.1970, 0.9589),
    ("2031-11-14","Hybrid", "Solar",  1.1,"Pacific Ocean (open ocean, very limited land)",       0.3078, 1.0106),
    ("2033-03-30","Total",  "Solar",  2.6,"E United States, Atlantic, W Africa",                 0.9778, 1.0462),
    ("2034-03-20","Total",  "Solar",  4.2,"Nigeria, Cameroon, Chad, Sudan, Egypt, Saudi, India, China", 0.2894, 1.0458),
    ("2034-09-12","Annular","Solar",  3.0,"S Pacific, Chile, Argentina, S Atlantic",            -0.3936, 0.9736),

    # ─── LUNAR ECLIPSES (Total + notable Partial, 2025-2034) ───
    # Source: eclipse.gsfc.nasa.gov/LEcat5/LE2001-2100.html
    # Duration = total phase (umbral) duration in minutes
    ("2025-03-14","Total",  "Lunar", 65.4,"Americas, Europe, Africa",                           0.3484, 1.1784),
    ("2025-09-07","Total",  "Lunar", 82.1,"Europe, Africa, Asia, Australia",                   -0.2752, 1.3619),
    ("2026-03-03","Total",  "Lunar", 58.3,"Americas, Europe, W Africa",                        -0.3765, 1.1507),
    ("2026-08-28","Partial","Lunar",  0.0,"Americas, Europe, Africa (93% umbral mag)",          0.4964, 0.9299),
    ("2028-07-06","Partial","Lunar",  0.0,"Americas, Atlantic, W Africa (39% umbral mag)",     -0.7903, 0.3892),
    ("2028-12-31","Total",  "Lunar", 71.3,"Americas, Europe, Africa, W Asia",                   0.3258, 1.2463),
    ("2029-06-26","Total",  "Lunar",101.9,"Americas, Europe, Africa — longest of the decade",   0.0124, 1.8436),
    ("2029-12-20","Total",  "Lunar", 53.7,"Americas, Europe, Africa, W Asia",                  -0.3811, 1.1174),
    ("2030-06-15","Partial","Lunar",  0.0,"Americas, Pacific (50% umbral mag)",                 0.7534, 0.5025),
    ("2032-04-25","Total",  "Lunar", 65.5,"Americas, E Pacific, NE Asia",                      -0.3558, 1.1913),
    ("2032-10-18","Total",  "Lunar", 47.1,"Europe, Africa, Asia, Australia, W Pacific",         0.4169, 1.1028),
    ("2033-04-14","Total",  "Lunar", 49.2,"Africa, Asia, Indian Ocean, Australia",              0.3954, 1.0944),
    ("2033-10-08","Total",  "Lunar", 78.8,"Americas, Europe, Africa, W Asia",                  -0.2889, 1.3497),
]

cols = ["eclipse_date","eclipse_type","body","duration_minutes",
        "path_description","gamma","magnitude"]
df = spark.createDataFrame(eclipses, cols)
df = (df.withColumn("eclipse_date", F.to_date("eclipse_date"))
        .withColumn("year", F.year("eclipse_date")))

df.write.format("delta").mode("overwrite").saveAsTable("cosmos.space.eclipse_catalog")
print(f"Loaded {df.count()} eclipse records (source: NASA GSFC Five Millennium Catalog)")
