import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# ============================================================
# Correct schema paths for your environment
# ============================================================
BRONZE_SCHEMA = "workspace.etl-bronze-pipelne-data"
SILVER_SCHEMA = "workspace.etl-silver-pipelne-data"

# ZIP lookup table in workspace.default
ZIP_TABLE = "workspace.default.us_zip_lookup"


# ============================================================
# Helper: UC-safe table existence check
# ============================================================
def table_exists(full_table_name: str) -> bool:
    try:
        spark.sql(f"DESCRIBE TABLE {full_table_name}")
        return True
    except:
        return False


# ============================================================
# Auto-discover all Bronze tables and unify them
# ============================================================
def load_all_bronze_tables(schema: str):
    # Split catalog.schema for proper quoting
    parts = schema.split(".")
    catalog = parts[0]
    schema_name = parts[1]
    quoted_schema = f"`{catalog}`.`{schema_name}`"

    tables = [
        row.tableName
        for row in spark.sql(f"SHOW TABLES IN {quoted_schema}").collect()
    ]

    dfs = []
    for t in tables:
        full_name = f"{quoted_schema}.`{t}`"
        df = spark.read.table(full_name)
        df = df.withColumn("source_table", F.lit(t))
        dfs.append(df)

    if not dfs:
        return spark.createDataFrame(
            [],
            "cust_id STRING, first_name STRING, last_name STRING, address STRING, city STRING, state STRING, zip DOUBLE, amount_paid STRING, _ingested_at TIMESTAMP, _source_file STRING, source_table STRING"
        )

    base_df = dfs[0]
    for df in dfs[1:]:
        base_df = base_df.unionByName(df, allowMissingColumns=True)

    return base_df


# ============================================================
# DLT Bronze (Unified)
# ============================================================
@dlt.table(
    name="customers_bronze_all",
    comment="Unified Bronze customer data from all workspace.default Bronze tables."
)
def customers_bronze_all():
    return load_all_bronze_tables(BRONZE_SCHEMA)


# ============================================================
# ZIP Lookup with Fallback
# ============================================================
@dlt.table(
    name="zip_lookup",
    comment="ZIP → City/State lookup with fallback if USPS table is missing."
)
def zip_lookup():
    if table_exists(ZIP_TABLE):
        return (
            spark.table(ZIP_TABLE)
            .select(
                F.col("zip").cast("string").alias("zip"),
                F.initcap("city").alias("city"),
                F.upper("state").alias("state")
            )
        )
    else:
        return spark.createDataFrame(
            [],
            "zip STRING, city STRING, state STRING"
        )


# ============================================================
# Silver Layer (Cleaning + Enrichment)
# ============================================================
@dlt.table(
    name="customers_silver_all",
    comment="Cleaned, standardized, ZIP-enriched customer data."
)
def customers_silver_all():
    df = dlt.read("customers_bronze_all")
    zip_df = dlt.read("zip_lookup")

    # Trim strings - cache schema to avoid multiple RPCs
    schema_dtypes = df.dtypes
    for c, t in schema_dtypes:
        if t == "string":
            df = df.withColumn(c, F.trim(F.col(c)))

    # Normalize names
    df = (
        df.withColumn("first_name", F.initcap("first_name"))
        .withColumn("last_name", F.initcap("last_name"))
        .withColumn("city", F.initcap("city"))
        .withColumn("state", F.upper("state"))
    )

    # Repair cust_id
    df = df.withColumn(
        "cust_id",
        F.when(
            F.col("cust_id").isNull() | (F.col("cust_id") == ""),
            F.concat(F.lit("CUST-AUTO-"), F.monotonically_increasing_id())
        ).otherwise(F.col("cust_id"))
    )

    # ZIP cleanup
    df = df.withColumn("zip_str", F.col("zip").cast("string"))
    df = df.withColumn("zip_str", F.regexp_replace("zip_str", "[^0-9]", ""))

    df = df.withColumn(
        "zip",
        F.when(F.length("zip_str") == 5, F.col("zip_str"))
        .when(F.length("zip_str") < 5, F.lpad("zip_str", 5, "0"))
        .otherwise(None)
    ).drop("zip_str")

    # amount_paid cleanup
    invalid_values = ["pending", "unknown", "n/a", "#ref!", "tbd", "void", "error", ""]

    df = df.withColumn(
        "amount_paid_clean",
        F.regexp_replace("amount_paid", "[$,]", "")
    )

    df = df.withColumn(
        "amount_paid",
        F.when(F.lower("amount_paid_clean").isin(invalid_values), None)
        .otherwise(F.expr("try_cast(amount_paid_clean AS DOUBLE)"))
    ).drop("amount_paid_clean")

    # ZIP lookup join (fallback-safe) - drop city/state before coalescing to avoid duplicates
    df = df.drop("city", "state")
    df = (
        df.alias("c")
        .join(zip_df.alias("z"), F.col("c.zip") == F.col("z.zip"), "left")
        .select(
            "c.*",
            F.col("z.city").alias("city"),
            F.col("z.state").alias("state")
        )
    )

    # Deduplicate per cust_id per source_table
    w = Window.partitionBy("cust_id", "source_table").orderBy(F.col("amount_paid").desc_nulls_last())
    df = (
        df.withColumn("rn", F.row_number().over(w))
        .filter("rn = 1")
        .drop("rn")
    )

    df = df.withColumn("silver_load_ts", F.current_timestamp())

    return df


# ============================================================
# Data Quality Report (DQR)
# ============================================================
@dlt.table(
    name="customers_silver_all_dqr",
    comment="Data quality report for customers_silver_all."
)
def customers_silver_all_dqr():
    df = dlt.read("customers_silver_all")

    # Cache schema to avoid multiple RPCs
    schema_columns = df.columns
    metrics = df.groupBy("source_table").agg(
        F.count("*").alias("row_count"),
        *[
            F.sum(F.col(c).isNull().cast("int")).alias(f"{c}_nulls")
            for c in schema_columns
        ],
    ).withColumn("report_ts", F.current_timestamp())

    return metrics


# ============================================================
# Gold Layer: RFM + CLV Segmentation
# ============================================================
@dlt.table(
    name="customers_gold_rfm_clv",
    comment="Gold layer: RFM metrics, CLV proxy, and segmentation."
)
def customers_gold_rfm_clv():
    df = dlt.read("customers_silver_all")

    tx = df.select(
        "cust_id",
        "amount_paid",
        "silver_load_ts"
    ).where(F.col("amount_paid").isNotNull())

    agg = tx.groupBy("cust_id").agg(
        F.max("silver_load_ts").alias("last_tx_ts"),
        F.count("*").alias("frequency"),
        F.sum("amount_paid").alias("monetary")
    )

    agg = agg.withColumn(
        "recency_days",
        F.expr("datediff(current_timestamp(), last_tx_ts)")
    )

    agg = agg.withColumn("clv_proxy", F.col("monetary"))

    agg = (
        agg.withColumn(
            "value_segment",
            F.when(F.col("monetary") >= 1000, "High")
            .when(F.col("monetary") >= 250, "Medium")
            .otherwise("Low")
        )
        .withColumn(
            "recency_segment",
            F.when(F.col("recency_days") <= 30, "Recent")
            .when(F.col("recency_days") <= 90, "Warm")
            .otherwise("Cold")
        )
        .withColumn(
            "frequency_segment",
            F.when(F.col("frequency") >= 10, "Frequent")
            .when(F.col("frequency") >= 3, "Occasional")
            .otherwise("Rare")
        )
    )

    return agg


# ============================================================
# Gold Summary Table
# ============================================================
@dlt.table(
    name="customers_gold_segments_summary",
    comment="Segment distribution summary for value, recency, and frequency bands."
)
def customers_gold_segments_summary():
    df = dlt.read("customers_gold_rfm_clv")

    summary = df.groupBy(
        "value_segment",
        "recency_segment",
        "frequency_segment"
    ).agg(
        F.count("*").alias("customer_count"),
        F.round(F.avg("monetary"), 2).alias("avg_monetary"),
        F.round(F.avg("clv_proxy"), 2).alias("avg_clv_proxy")
    ).withColumn("report_ts", F.current_timestamp())

    return summary
