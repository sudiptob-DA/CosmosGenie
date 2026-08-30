"Gold: Cosmic KPIs - one-row summary for the app KPI bar."
from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.materialized_view(
    name="gold_cosmic_kpis",
    comment="Single-row KPI summary: asteroids this week, hazardous, next eclipse, etc.",
)
def gold_cosmic_kpis():
    today = F.current_date()
    week_end = F.date_add(today, 7)

    asteroids = (
        spark.read.table("neo_close_approaches")
        .filter((F.col("approach_date") >= today) & (F.col("approach_date") <= week_end))
        .agg(F.count("*").alias("asteroids_this_week"),
             F.sum(F.when(F.col("is_potentially_hazardous")==True,1).otherwise(0)).alias("hazardous_count")))

    eclipse = (
        spark.read.table("cosmos.space.eclipse_catalog")
        .filter(F.col("eclipse_date") >= today).orderBy("eclipse_date").limit(1)
        .select(F.datediff("eclipse_date",today).alias("days_to_eclipse"),
                F.concat(F.col("eclipse_type"),F.lit(" "),F.col("body")).alias("next_eclipse_type")))

    event = (
        spark.read.table("cosmos.space.planetary_events")
        .filter(F.col("event_date") >= today).orderBy("event_date").limit(1)
        .select(F.datediff("event_date",today).alias("days_to_alignment"),
                F.col("event_type").alias("next_event_type")))

    weather = (
        spark.read.table("space_weather_events")
        .filter(F.col("event_type")=="GST").orderBy(F.col("begin_time").desc()).limit(1)
        .select(F.col("class_type").alias("latest_storm_scale")))

    moon = (
        spark.read.table("cosmos.space.moon_phases")
        .filter((F.col("phase_name")=="Full Moon") & (F.col("phase_date") >= today))
        .orderBy("phase_date").limit(1)
        .select(F.datediff("phase_date",today).alias("days_to_full_moon")))

    return asteroids.crossJoin(eclipse).crossJoin(event).crossJoin(weather).crossJoin(moon)
