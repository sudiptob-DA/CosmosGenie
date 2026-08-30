"Gold: Approaching asteroids next 30 days."
from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.materialized_view(
    name="gold_asteroid_alerts",
    comment="Asteroids approaching Earth within 30 days, ranked by proximity.",
)
@dp.expect("has_approach_date", "approach_date IS NOT NULL")
def gold_asteroid_alerts():
    return (
        spark.read.table("neo_close_approaches")
        .filter(
            (F.col("approach_date") >= F.current_date())
            & (F.col("approach_date") <= F.date_add(F.current_date(), 30))
        )
        .withColumn("miss_distance_lunar", F.round(F.col("miss_distance_au") / 0.00257, 1))
        .withColumn("threat_level",
            F.when((F.col("is_potentially_hazardous") == True) & (F.col("miss_distance_lunar") < 20), "HIGH")
            .when(F.col("is_potentially_hazardous") == True, "WATCH")
            .otherwise("SAFE"))
        .withColumn("size_estimate",
            F.concat(F.round(F.col("diameter_min_m"), 0).cast("string"), F.lit("-"),
                     F.round(F.col("diameter_max_m"), 0).cast("string"), F.lit("m")))
        .select("asteroid_id","name","approach_date","miss_distance_au","miss_distance_km",
                "miss_distance_lunar","velocity_kps","size_estimate",
                "is_potentially_hazardous","threat_level","absolute_magnitude")
        .orderBy("approach_date","miss_distance_au")
    )
