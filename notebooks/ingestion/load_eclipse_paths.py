# Databricks notebook source
# MAGIC %md
# MAGIC # load_eclipse_paths — One-time Static Load

# COMMAND ----------

from pyspark.sql import functions as F

paths_2027 = [
  ("Luxor","Egypt","N Africa",25.69,32.64,383,8,"LXR",99,"BEST: 6m 23s, 99% clear, near centerline"),
  ("Aswan","Egypt","N Africa",24.09,32.89,360,25,"ASW",99,"6m totality, near centerline, guaranteed clear"),
  ("Cairo","Egypt","N Africa",30.06,31.24,330,80,"CAI",93,"5m 30s, world-class infrastructure"),
  ("Sfax","Tunisia","N Africa",34.74,10.76,300,30,"SFA",86,"5m, very close to centerline"),
  ("Marrakech","Morocco","N Africa",31.63,-7.99,280,140,"RAK",85,"4.5m, major tourist hub"),
  ("Tunis","Tunisia","N Africa",36.82,10.17,250,150,"TUN",80,"4m+, strong European flight links"),
  ("Jeddah","Saudi Arabia","Middle East",21.54,39.17,300,90,"JED",90,"Open international city, 5m"),
  ("Alexandria","Egypt","Middle East",31.20,29.92,350,40,"ALY",88,"Major Egyptian city, 5m+"),
]

paths_2028 = [
  ("Broken Hill","Australia","NSW",-31.95,141.43,220,40,"BHQ",82,"Best odds: 3.5m, clear inland skies"),
  ("Dubbo","Australia","NSW",-32.25,148.60,205,55,"DBO",75,"3.5m, regional hub"),
  ("Sydney","Australia","NSW",-33.87,151.21,150,15,"SYD",55,"First since 1857! Coastal cloud risk"),
  ("Queenstown","New Zealand","Otago",-45.03,168.66,160,20,"ZQN",55,"2.5m, stunning alpine backdrop"),
  ("Canberra","Australia","ACT",-35.28,149.13,120,50,"CBR",65,"2m, inland capital, better sky odds"),
]

cols = ["city_name","country","region","latitude","longitude",
        "totality_duration_sec","dist_from_centerline_km","nearest_airport_code",
        "sky_clarity_pct","viewing_notes"]

df27 = spark.createDataFrame([("2027-08-02",)+r for r in paths_2027], ["eclipse_date"]+cols)
df28 = spark.createDataFrame([("2028-07-22",)+r for r in paths_2028], ["eclipse_date"]+cols)

df = (df27.union(df28).withColumn("eclipse_date", F.to_date("eclipse_date")))
df.write.format("delta").mode("overwrite").saveAsTable("cosmos.space.eclipse_paths")
print(f"Loaded {df.count()} eclipse path records")

