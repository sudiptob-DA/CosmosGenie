"""Silver: neo_close_approaches - cleaned, typed, with data quality checks."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.materialized_view(
    name="neo_close_approaches",
    comment="Cleaned asteroid close-approach data with quality expectations",
)
@dp.expect("valid_distance", "miss_distance_au > 0")
@dp.expect("valid_approach_date", "approach_date IS NOT NULL")
def neo_close_approaches():
    return (
        spark.read.table("bronze_neo_close_approaches")
        .withColumn("approach_date", F.to_date("approach_date"))
        .withColumn("fetched_at", F.to_timestamp("fetched_at"))
        .select(
            F.col("asteroid_id").cast("string"),
            F.col("name").cast("string"),
            "approach_date",
            F.col("miss_distance_au").cast("double"),
            F.col("miss_distance_km").cast("double"),
            F.col("velocity_kps").cast("double"),
            F.col("diameter_min_m").cast("double"),
            F.col("diameter_max_m").cast("double"),
            F.col("is_potentially_hazardous").cast("boolean"),
            F.col("absolute_magnitude").cast("double"),
            "fetched_at",
        )
    )
