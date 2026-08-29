"""Silver: space_weather_events - cleaned, typed, with data quality checks."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.materialized_view(
    name="space_weather_events",
    comment="Cleaned space weather events with quality expectations",
)
@dp.expect("valid_event_type", "event_type IN ('FLR', 'GST')")
@dp.expect("valid_begin_time", "begin_time IS NOT NULL")
def space_weather_events():
    return (
        spark.read.table("bronze_space_weather_events")
        .withColumn("begin_time", F.to_timestamp("begin_time"))
        .withColumn("peak_time", F.to_timestamp("peak_time"))
        .withColumn("end_time", F.to_timestamp("end_time"))
        .withColumn("fetched_at", F.to_timestamp("fetched_at"))
        .select(
            F.col("event_id").cast("string"),
            F.col("event_type").cast("string"),
            "begin_time",
            "peak_time",
            "end_time",
            F.col("class_type").cast("string"),
            F.col("active_region").cast("int"),
            F.col("kp_index").cast("double"),
            "fetched_at",
        )
    )
