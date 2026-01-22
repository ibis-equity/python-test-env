"""
Kafka to Oracle Streaming Pipeline Examples

Demonstrates various streaming scenarios:
1. Basic stream read and write
2. Stream with transformations
3. Stream with windowing and aggregations
4. Stream with data quality checks
5. Stream with deduplication
6. Multi-topic streaming with joins
7. Complex ETL with schema evolution
8. Error handling and recovery
"""

import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct,
    current_timestamp, window, count, sum, avg,
    explode, split, regexp_extract
)
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, IntegerType

from kafka_oracle_streaming import (
    KafkaOracleStreamingPipeline,
    KafkaConfig,
    OracleConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== Example 1: Basic Stream Read and Write ====================

def example_basic_stream():
    """
    Example 1: Basic Kafka to Oracle streaming
    - Read from Kafka topic
    - Write to Oracle table
    """
    logger.info("Starting Example 1: Basic Stream Read and Write")
    
    # Create Spark session
    spark = SparkSession.builder \
        .appName("KafkaOracleBasic") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    # Configure Kafka and Oracle
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="orders",
        group_id="oracle-consumer"
    )
    
    oracle_config = OracleConfig(
        host="localhost",
        port=1521,
        service_name="XE",
        user="system",
        password="oracle"
    )
    
    # Create pipeline
    pipeline = KafkaOracleStreamingPipeline(
        spark=spark,
        kafka_config=kafka_config,
        oracle_config=oracle_config,
        app_name="BasicStreaming"
    )
    
    # Read from Kafka
    df_stream = pipeline.read_kafka_stream()
    
    # Write to Oracle
    query = pipeline.write_to_oracle(
        df=df_stream,
        table_name="orders_stream",
        trigger_interval="30 seconds"
    )
    
    # Wait for termination
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        logger.info("Stopping stream")
        pipeline.stop_all_streams()


# ==================== Example 2: Stream with Transformations ====================

def example_stream_with_transformations():
    """
    Example 2: Stream with data transformations
    - Parse JSON from Kafka
    - Apply business logic transformations
    - Add metadata
    """
    logger.info("Starting Example 2: Stream with Transformations")
    
    spark = SparkSession.builder \
        .appName("KafkaOracleTransform") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    # Define schema for incoming JSON
    order_schema = StructType([
        StructField("order_id", StringType()),
        StructField("customer_id", StringType()),
        StructField("amount", DoubleType()),
        StructField("product_category", StringType()),
        StructField("order_date", StringType())
    ])
    
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="orders",
        group_id="transform-consumer"
    )
    
    oracle_config = OracleConfig(
        host="localhost",
        port=1521,
        service_name="XE",
        user="system",
        password="oracle"
    )
    
    pipeline = KafkaOracleStreamingPipeline(
        spark=spark,
        kafka_config=kafka_config,
        oracle_config=oracle_config,
        app_name="TransformStreaming"
    )
    
    # Read stream with schema
    df_stream = pipeline.read_kafka_stream(schema=order_schema)
    
    # Apply transformations
    def transform_orders(df):
        """Transform order data"""
        return df \
            .withColumn("amount_usd", col("amount") * 1.1) \
            .withColumn("order_year", regexp_extract(col("order_date"), r"(\d{4})", 1)) \
            .withColumn("high_value", col("amount") > 1000)
    
    df_transformed = pipeline.apply_transformation(df_stream, transform_orders)
    
    # Add processing metadata
    df_with_metadata = pipeline.add_processing_metadata(df_transformed)
    
    # Write to Oracle
    query = pipeline.write_to_oracle(
        df=df_with_metadata,
        table_name="orders_processed"
    )
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        pipeline.stop_all_streams()


# ==================== Example 3: Stream with Windowing & Aggregations ====================

def example_windowing_and_aggregations():
    """
    Example 3: Time-windowed aggregations
    - Apply 5-minute tumbling windows
    - Calculate aggregate metrics (sum, avg, count)
    - Write aggregated results
    """
    logger.info("Starting Example 3: Windowing and Aggregations")
    
    spark = SparkSession.builder \
        .appName("KafkaOracleWindow") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    order_schema = StructType([
        StructField("order_id", StringType()),
        StructField("customer_id", StringType()),
        StructField("amount", DoubleType()),
        StructField("order_date", StringType()),
        StructField("timestamp", StringType())
    ])
    
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="orders",
        group_id="window-consumer"
    )
    
    oracle_config = OracleConfig(
        host="localhost",
        port=1521,
        service_name="XE",
        user="system",
        password="oracle"
    )
    
    pipeline = KafkaOracleStreamingPipeline(
        spark=spark,
        kafka_config=kafka_config,
        oracle_config=oracle_config,
        app_name="WindowedStreaming"
    )
    
    # Read stream
    df_stream = pipeline.read_kafka_stream(schema=order_schema)
    
    # Apply windowing
    df_windowed = pipeline.apply_windowing(
        df=df_stream,
        timestamp_col="timestamp",
        window_duration="5 minutes"
    )
    
    # Aggregate within windows
    df_aggregated = df_windowed \
        .groupBy("time_window") \
        .agg(
            count("order_id").alias("order_count"),
            sum("amount").alias("total_amount"),
            avg("amount").alias("avg_amount")
        ) \
        .select(
            col("time_window.start").alias("window_start"),
            col("time_window.end").alias("window_end"),
            col("order_count"),
            col("total_amount"),
            col("avg_amount")
        )
    
    # Write to Oracle
    query = pipeline.write_to_oracle(
        df=df_aggregated,
        table_name="order_metrics_5min"
    )
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        pipeline.stop_all_streams()


# ==================== Example 4: Stream with Data Quality Checks ====================

def example_data_quality_checks():
    """
    Example 4: Stream with data quality validation
    - Add quality check columns
    - Filter invalid records
    - Write to separate tables
    """
    logger.info("Starting Example 4: Data Quality Checks")
    
    spark = SparkSession.builder \
        .appName("KafkaOracleQuality") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    order_schema = StructType([
        StructField("order_id", StringType()),
        StructField("customer_id", StringType()),
        StructField("amount", DoubleType()),
        StructField("email", StringType())
    ])
    
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="orders",
        group_id="quality-consumer"
    )
    
    oracle_config = OracleConfig(
        host="localhost",
        port=1521,
        service_name="XE",
        user="system",
        password="oracle"
    )
    
    pipeline = KafkaOracleStreamingPipeline(
        spark=spark,
        kafka_config=kafka_config,
        oracle_config=oracle_config,
        app_name="QualityStreaming"
    )
    
    # Read stream
    df_stream = pipeline.read_kafka_stream(schema=order_schema)
    
    # Define quality rules
    quality_rules = {
        "valid_order_id": lambda df: col("order_id").isNotNull(),
        "valid_amount": lambda df: (col("amount") > 0) & (col("amount") < 100000),
        "valid_email": lambda df: col("email").rlike("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    }
    
    # Add quality checks
    df_with_quality = pipeline.add_data_quality_checks(df_stream, quality_rules)
    
    # Split into good and bad records
    df_good = df_with_quality.filter(
        col("quality_valid_order_id") & 
        col("quality_valid_amount") & 
        col("quality_valid_email")
    )
    
    df_bad = df_with_quality.filter(
        ~col("quality_valid_order_id") | 
        ~col("quality_valid_amount") | 
        ~col("quality_valid_email")
    )
    
    # Write good records
    query_good = pipeline.write_to_oracle(
        df=df_good,
        table_name="orders_validated"
    )
    
    # Write bad records for investigation
    query_bad = pipeline.write_to_oracle(
        df=df_bad,
        table_name="orders_invalid"
    )
    
    try:
        query_good.awaitTermination()
    except KeyboardInterrupt:
        pipeline.stop_all_streams()


# ==================== Example 5: Stream with Deduplication ====================

def example_stream_deduplication():
    """
    Example 5: Remove duplicates from stream
    - Apply watermark for late data
    - Deduplicate on key columns
    - Write deduplicated records
    """
    logger.info("Starting Example 5: Stream Deduplication")
    
    spark = SparkSession.builder \
        .appName("KafkaOracleDedup") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    order_schema = StructType([
        StructField("order_id", StringType()),
        StructField("transaction_id", StringType()),
        StructField("customer_id", StringType()),
        StructField("amount", DoubleType())
    ])
    
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="transactions",
        group_id="dedup-consumer"
    )
    
    oracle_config = OracleConfig(
        host="localhost",
        port=1521,
        service_name="XE",
        user="system",
        password="oracle"
    )
    
    pipeline = KafkaOracleStreamingPipeline(
        spark=spark,
        kafka_config=kafka_config,
        oracle_config=oracle_config,
        app_name="DeduplicationStreaming"
    )
    
    # Read stream
    df_stream = pipeline.read_kafka_stream(schema=order_schema)
    
    # Deduplicate on transaction_id within 1-hour window
    df_dedup = pipeline.deduplicate_stream(
        df=df_stream,
        subset=["transaction_id"],
        within_window="1 hour"
    )
    
    # Write to Oracle
    query = pipeline.write_to_oracle(
        df=df_dedup,
        table_name="transactions_deduplicated"
    )
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        pipeline.stop_all_streams()


# ==================== Example 6: Multi-Topic Streaming ====================

def example_multi_topic_streaming():
    """
    Example 6: Stream from multiple Kafka topics
    - Read from orders and customers topics
    - Join streams
    - Write enriched data
    """
    logger.info("Starting Example 6: Multi-Topic Streaming")
    
    spark = SparkSession.builder \
        .appName("KafkaOracleMultiTopic") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    # Schemas
    order_schema = StructType([
        StructField("order_id", StringType()),
        StructField("customer_id", StringType()),
        StructField("amount", DoubleType())
    ])
    
    customer_schema = StructType([
        StructField("customer_id", StringType()),
        StructField("customer_name", StringType()),
        StructField("segment", StringType())
    ])
    
    # Kafka configs
    kafka_orders = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="orders",
        group_id="orders-consumer"
    )
    
    kafka_customers = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="customers",
        group_id="customers-consumer"
    )
    
    oracle_config = OracleConfig(
        host="localhost",
        port=1521,
        service_name="XE",
        user="system",
        password="oracle"
    )
    
    # Create pipelines for each topic
    pipeline = KafkaOracleStreamingPipeline(
        spark=spark,
        kafka_config=kafka_orders,
        oracle_config=oracle_config,
        app_name="MultiTopicStreaming"
    )
    
    # Read orders stream
    df_orders = pipeline.read_kafka_stream(schema=order_schema)
    
    # Read customers stream (batch read from Kafka)
    pipeline.kafka_config = kafka_customers
    df_customers = pipeline.read_kafka_stream(schema=customer_schema)
    
    # Join streams
    df_enriched = df_orders.join(
        df_customers,
        on="customer_id",
        how="left"
    )
    
    # Switch back to orders config for writing
    pipeline.kafka_config = kafka_orders
    
    # Write enriched data
    query = pipeline.write_to_oracle(
        df=df_enriched,
        table_name="orders_enriched"
    )
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        pipeline.stop_all_streams()


# ==================== Example 7: Complex ETL Pipeline ====================

def example_complex_etl_pipeline():
    """
    Example 7: Complex ETL with multiple transformations
    - Extract from Kafka
    - Transform with business logic
    - Validate and clean
    - Load to Oracle
    """
    logger.info("Starting Example 7: Complex ETL Pipeline")
    
    spark = SparkSession.builder \
        .appName("KafkaOracleComplexETL") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    event_schema = StructType([
        StructField("event_id", StringType()),
        StructField("event_type", StringType()),
        StructField("user_id", StringType()),
        StructField("timestamp", StringType()),
        StructField("data", StringType())
    ])
    
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="events",
        group_id="etl-consumer"
    )
    
    oracle_config = OracleConfig(
        host="localhost",
        port=1521,
        service_name="XE",
        user="system",
        password="oracle"
    )
    
    pipeline = KafkaOracleStreamingPipeline(
        spark=spark,
        kafka_config=kafka_config,
        oracle_config=oracle_config,
        app_name="ComplexETL"
    )
    
    # Step 1: Extract from Kafka
    df_raw = pipeline.read_kafka_stream(schema=event_schema)
    
    # Step 2: Transform
    def etl_transformation(df):
        return df \
            .filter(col("event_type").isNotNull()) \
            .withColumn("processed_at", current_timestamp()) \
            .withColumn("year", regexp_extract(col("timestamp"), r"(\d{4})", 1)) \
            .withColumn("month", regexp_extract(col("timestamp"), r"-(\d{2})", 1))
    
    df_transformed = pipeline.apply_transformation(df_raw, etl_transformation)
    
    # Step 3: Validate schema
    expected_cols = {
        "event_id": "string",
        "event_type": "string",
        "user_id": "string"
    }
    is_valid, errors = pipeline.validate_stream_schema(df_transformed, expected_cols)
    
    if not is_valid:
        logger.warning(f"Schema validation errors: {errors}")
    
    # Step 4: Add metadata
    df_with_metadata = pipeline.add_processing_metadata(df_transformed)
    
    # Step 5: Load to Oracle
    query = pipeline.write_to_oracle(
        df=df_with_metadata,
        table_name="events_processed"
    )
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        pipeline.stop_all_streams()


# ==================== Example 8: Error Handling and Recovery ====================

def example_error_handling():
    """
    Example 8: Stream with error handling and recovery
    - Enable checkpointing for fault tolerance
    - Handle errors gracefully
    - Monitor stream health
    """
    logger.info("Starting Example 8: Error Handling and Recovery")
    
    spark = SparkSession.builder \
        .appName("KafkaOracleErrorHandling") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    order_schema = StructType([
        StructField("order_id", StringType()),
        StructField("amount", DoubleType())
    ])
    
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="orders",
        group_id="error-consumer"
    )
    
    oracle_config = OracleConfig(
        host="localhost",
        port=1521,
        service_name="XE",
        user="system",
        password="oracle"
    )
    
    pipeline = KafkaOracleStreamingPipeline(
        spark=spark,
        kafka_config=kafka_config,
        oracle_config=oracle_config,
        app_name="ErrorHandlingStreaming"
    )
    
    # Enable fault tolerance
    pipeline.enable_fault_tolerance(
        checkpoint_dir="/tmp/kafka_oracle_checkpoint",
        log_dir="/tmp/kafka_oracle_logs"
    )
    
    # Read stream
    df_stream = pipeline.read_kafka_stream(schema=order_schema)
    
    # Write with error handling
    query = pipeline.write_to_oracle(
        df=df_stream,
        table_name="orders_resilient",
        checkpoint_location="/tmp/kafka_oracle_checkpoint/orders"
    )
    
    # Monitor stream
    try:
        import threading
        monitor_thread = threading.Thread(
            target=pipeline.monitor_streams,
            kwargs={"interval": 60},
            daemon=True
        )
        monitor_thread.start()
        
        query.awaitTermination()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        pipeline.stop_all_streams()


# ==================== Main ====================

if __name__ == "__main__":
    """
    Run examples
    
    Uncomment the example you want to run:
    """
    
    # Example 1: Basic streaming
    # example_basic_stream()
    
    # Example 2: Stream with transformations
    # example_stream_with_transformations()
    
    # Example 3: Windowing and aggregations
    # example_windowing_and_aggregations()
    
    # Example 4: Data quality checks
    # example_data_quality_checks()
    
    # Example 5: Stream deduplication
    # example_stream_deduplication()
    
    # Example 6: Multi-topic streaming
    # example_multi_topic_streaming()
    
    # Example 7: Complex ETL pipeline
    # example_complex_etl_pipeline()
    
    # Example 8: Error handling and recovery
    # example_error_handling()
    
    logger.info("Examples ready to run. Uncomment desired example to execute.")
