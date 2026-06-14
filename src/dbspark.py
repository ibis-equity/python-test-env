from pyspark.sql import functions as F
from datetime import datetime

SOURCE_SCHEMA = "workspace.`etl-bronze-pipelne-data`"
ARCHIVE_SCHEMA = "workspace.`etl-bronze-pipelne-processed-raw-data`"
AUDIT_TABLE = "workspace.default.bronze_archive_audit"


def ensure_schema(schema_name: str):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")


def ensure_audit_table():
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {AUDIT_TABLE} (
            table_name STRING,
            archived_at TIMESTAMP,
            row_count BIGINT,
            status STRING,
            message STRING
        )
    """)


def table_exists(full_name: str) -> bool:
    try:
        spark.sql(f"DESCRIBE TABLE {full_name}")
        return True
    except:
        return False


def archive_processed_bronze_tables():
    ensure_schema(ARCHIVE_SCHEMA)
    ensure_audit_table()

    # List all tables in the Bronze schema
    bronze_tables = [
        row.tableName
        for row in spark.sql(f"SHOW TABLES IN {SOURCE_SCHEMA}").collect()
    ]

    # List all tables that DLT successfully processed (Silver layer)
    processed_tables = [
        row.tableName
        for row in spark.sql("SHOW TABLES IN workspace.default").collect()
        if row.tableName.startswith("customers_silver_all")
    ]

    # Extract source_table names from Silver
    silver_df = spark.table("workspace.default.customers_silver_all")
    successful_sources = [r.source_table for r in silver_df.select("source_table").distinct().collect()]

    for table_name in bronze_tables:
        full_source = f"{SOURCE_SCHEMA}.`{table_name}`"
        full_archive = f"{ARCHIVE_SCHEMA}.`{table_name}`"

        if table_name not in successful_sources:
            # Log skipped tables
            spark.sql(f"""
                INSERT INTO {AUDIT_TABLE}
                VALUES ('{table_name}', current_timestamp(), NULL, 'SKIPPED', 'Not processed by DLT')
            """)
            continue

        try:
            # Count rows before archiving
            row_count = spark.table(full_source).count()

            # Move table (CTAS)
            spark.sql(f"CREATE TABLE {full_archive} AS SELECT * FROM {full_source}")

            # Drop original
            spark.sql(f"DROP TABLE {full_source}")

            # Log success
            spark.sql(f"""
                INSERT INTO {AUDIT_TABLE}
                VALUES ('{table_name}', current_timestamp(), {row_count}, 'ARCHIVED', 'Success')
            """)

            print(f"Archived {full_source} → {full_archive}")

        except Exception as e:
            # Log failure
            spark.sql(f"""
                INSERT INTO {AUDIT_TABLE}
                VALUES ('{table_name}', current_timestamp(), NULL, 'FAILED', '{str(e)}')
            """)
            print(f"Failed to archive {full_source}: {e}")


# Run the archiver
archive_processed_bronze_tables()