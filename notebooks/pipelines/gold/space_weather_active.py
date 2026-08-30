"Gold: Significant space weather events last 30 days."
from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.materialized_view(
    name="gold_space_weather_active",
    comment="Significant space weather: G2+ storms, M/X-class flares, last 30 days.",
)
@dp.expect("valid_event_type", "event_type IN ('FLR', 'GST')")
def gold_space_weather_active():
    return (
        spark.read.table("space_weather_events")
        .filter(F.col("begin_time") >= F.date_sub(F.current_date(), 30))
        .withColumn("severity",
            F.when(F.col("class_type").startswith("X"), "EXTREME")
            .when(F.col("class_type").startswith("M"), "STRONG")
            .when(F.col("class_type").isin("G5","G4","G3"), "SEVERE")
            .when(F.col("class_type") == "G2", "MODERATE")
            .when(F.col("class_type") == "G1", "MINOR")
            .otherwise("LOW"))
        .withColumn("aurora_likelihood",
            F.when(F.col("class_type").isin("G3","G4","G5"), "HIGH - visible at mid-latitudes")
            .when(F.col("class_type") == "G2", "MODERATE - visible at high latitudes")
            .when(F.col("class_type") == "G1", "LOW - visible near poles")
            .otherwise("UNLIKELY"))
        .select("event_id","event_type","begin_time","peak_time",
                "class_type","severity","kp_index","aurora_likelihood")
        .orderBy(F.col("begin_time").desc())
    )
