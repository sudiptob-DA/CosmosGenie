"Gold: Unified cosmic events timeline - next 12 months."
from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.materialized_view(
    name="gold_upcoming_events",
    comment="Unified timeline: eclipses + planetary events + launches, next 12 months.",
)
def gold_upcoming_events():
    today = F.current_date()
    one_year = F.date_add(today, 365)

    eclipses = (
        spark.read.table("cosmos.space.eclipse_catalog")
        .filter((F.col("eclipse_date") >= today) & (F.col("eclipse_date") <= one_year))
        .select(
            F.col("eclipse_date").alias("event_date"),
            F.lit("Eclipse").alias("category"),
            F.concat(F.col("eclipse_type"),F.lit(" "),F.col("body"),F.lit(" Eclipse")).alias("event_name"),
            F.col("path_description").alias("description"),
            F.col("duration_minutes")))

    planetary = (
        spark.read.table("cosmos.space.planetary_events")
        .filter((F.col("event_date") >= today) & (F.col("event_date") <= one_year))
        .select("event_date",
            F.col("event_type").alias("category"),
            F.concat(F.col("primary_body"),
                F.when(F.col("secondary_body").isNotNull(),
                    F.concat(F.lit(" & "),F.col("secondary_body"))).otherwise(F.lit("")),
                F.lit(" - "),F.col("event_type")).alias("event_name"),
            F.col("description"),
            F.lit(None).cast("double").alias("duration_minutes")))

    launches = (
        spark.read.table("cosmos.space.mission_launches")
        .filter((F.col("launch_date") >= today) & (F.col("launch_date") <= one_year)
                & F.col("status").isin("Go","TBD"))
        .select(
            F.col("launch_date").cast("date").alias("event_date"),
            F.lit("Launch").alias("category"),
            F.col("name").alias("event_name"),
            F.concat(F.col("agency"),F.lit(" - "),F.col("rocket"),
                F.when(F.col("is_crewed")==True,F.lit(" [CREWED]")).otherwise(F.lit("")),
                F.when(F.col("is_moon_mission")==True,F.lit(" [MOON]")).otherwise(F.lit("")))
            .alias("description"),
            F.lit(None).cast("double").alias("duration_minutes")))

    return (eclipses.unionByName(planetary).unionByName(launches)
            .withColumn("days_until", F.datediff("event_date", today))
            .orderBy("event_date"))
