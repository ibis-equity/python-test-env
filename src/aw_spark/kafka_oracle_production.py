"""
Complete End-to-End Kafka to Oracle Streaming Example

This example demonstrates:
1. Reading orders from Kafka
2. Processing and enriching data
3. Applying quality checks
4. Windowing and aggregations
5. Writing to Oracle
6. Monitoring and error handling
"""

import logging
import threading
import sys
from typing import Dict, Any
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct,
    current_timestamp, window, count, sum as spark_sum,
    avg, regexp_extract, when, length
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, 
    IntegerType, TimestampType
)

# Add src to path
import sys
sys.path.insert(0, 'c:/Users/desha/Python Projects/python-test-env/src')

from aw_spark.kafka_oracle_streaming import (
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


# ==================== Configuration ====================

class ProductionConfig:
    """Production configuration"""
    
    # Kafka configuration
    KAFKA_BROKERS = "kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9092"
    KAFKA_TOPICS = "orders,order-updates"
    KAFKA_GROUP = "oracle-consumer-prod"
    KAFKA_START_OFFSET = "earliest"
    
    # Oracle configuration
    ORACLE_HOST = "oracle-db.example.com"
    ORACLE_PORT = 1521
    ORACLE_SERVICE = "PROD"
    ORACLE_USER = "streaming_app"
    ORACLE_PASSWORD = "${ORACLE_PASSWORD}"  # From env var
    
    # Spark configuration
    SPARK_DRIVER_MEMORY = "4g"
    SPARK_EXECUTOR_MEMORY = "4g"
    SPARK_EXECUTORS = 4
    SPARK_PARTITIONS = 200
    
    # Streaming configuration
    CHECKPOINT_DIR = "/mnt/persistent/kafka-oracle-checkpoints"
    BATCH_INTERVAL = "30 seconds"
    WATERMARK_DELAY = "10 minutes"
    
    # Monitoring
    MONITORING_INTERVAL = 60  # seconds
    METRICS_PORT = 8000
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        import os
        cls.ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "oracle")
        cls.KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", cls.KAFKA_BROKERS)
        cls.ORACLE_HOST = os.getenv("ORACLE_HOST", cls.ORACLE_HOST)
        return cls


# ==================== Schema Definitions ====================

class Schemas:
    """Schema definitions for Kafka messages"""
    
    @staticmethod
    def order_schema() -> StructType:
        """Schema for order events"""
        return StructType([
            StructField("order_id", StringType(), False),
            StructField("customer_id", StringType(), False),
            StructField("order_date", StringType(), False),
            StructField("amount", DoubleType(), False),
            StructField("currency", StringType(), True),
            StructField("product_ids", StringType(), False),  # comma-separated
            StructField("shipping_address", StringType(), True),
            StructField("status", StringType(), False),
            StructField("timestamp", TimestampType(), False)
        ])
    
    @staticmethod
    def order_update_schema() -> StructType:
        """Schema for order update events"""
        return StructType([
            StructField("order_id", StringType(), False),
            StructField("update_type", StringType(), False),  # shipped, delivered, cancelled
            StructField("update_date", StringType(), False),
            StructField("notes", StringType(), True),
            StructField("timestamp", TimestampType(), False)
        ])


# ==================== Data Transformations ====================

def transform_order_data(df):
    """Apply business logic transformations to orders"""
    logger.info("Applying order transformations")
    
    return df \
        .withColumn("currency", when(col("currency").isNull(), "USD").otherwise(col("currency"))) \
        .withColumn("amount_usd", 
                   when(col("currency") == "USD", col("amount"))
                   .otherwise(col("amount") * 1.1)) \
        .withColumn("order_year", regexp_extract(col("order_date"), r"(\d{4})", 1)) \
        .withColumn("order_month", regexp_extract(col("order_date"), r"-(\d{2})", 1)) \
        .withColumn("high_value", col("amount") > 5000) \
        .withColumn("product_count", 
                   (length(col("product_ids")) - length(col("product_ids").replace(",", "")) + 1).cast(IntegerType())) \
        .withColumn("has_shipping", col("shipping_address").isNotNull())


# ==================== Quality Rules ====================

def get_quality_rules() -> Dict[str, Any]:
    """Define data quality rules"""
    return {
        "valid_order_id": lambda df: col("order_id").isNotNull() & (length(col("order_id")) > 0),
        "valid_customer_id": lambda df: col("customer_id").isNotNull(),
        "valid_amount": lambda df: (col("amount") > 0) & (col("amount") < 1000000),
        "valid_status": lambda df: col("status").isin(["pending", "processing", "shipped", "delivered", "cancelled"]),
        "valid_date_format": lambda df: regexp_extract(col("order_date"), r"^\d{4}-\d{2}-\d{2}$").isNotNull()
    }


# ==================== Monitoring ====================

class StreamingMonitor:
    """Monitor streaming pipelines"""
    
    def __init__(self, pipeline: KafkaOracleStreamingPipeline, interval: int = 60):
        self.pipeline = pipeline
        self.interval = interval
        self.metrics_history = []
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current metrics"""
        try:
            status = self.pipeline.get_stream_status()
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "pipeline_status": status["pipeline_status"],
                "streams": {}
            }
            
            for stream_name, stream_data in status["streams"].items():
                progress = stream_data["progress"]
                if progress:
                    metrics["streams"][stream_name] = {
                        "active": stream_data["active"],
                        "input_rate": progress.get("inputRowsPerSecond", 0),
                        "processing_rate": progress.get("processedRowsPerSecond", 0),
                        "total_input": progress.get("numInputRows", 0),
                        "total_processed": progress.get("numProcessedRows", 0),
                        "batch_duration_ms": progress.get("batchDuration", 0)
                    }
            
            return metrics
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            return {}
    
    def print_metrics(self, metrics: Dict[str, Any]) -> None:
        """Print formatted metrics"""
        print("\n" + "=" * 80)
        print(f"Streaming Pipeline Metrics - {metrics['timestamp']}")
        print(f"Status: {metrics['pipeline_status']}")
        print("=" * 80)
        
        for stream_name, stream_metrics in metrics.get("streams", {}).items():
            print(f"\nStream: {stream_name}")
            print(f"  Active: {stream_metrics['active']}")
            print(f"  Input Rate: {stream_metrics['input_rate']:.2f} rows/sec")
            print(f"  Processing Rate: {stream_metrics['processing_rate']:.2f} rows/sec")
            print(f"  Total Input: {stream_metrics['total_input']:,} rows")
            print(f"  Total Processed: {stream_metrics['total_processed']:,} rows")
            print(f"  Batch Duration: {stream_metrics['batch_duration_ms']}ms")
        
        print("=" * 80 + "\n")
    
    def start_monitoring(self) -> None:
        """Start background monitoring"""
        def monitor_loop():
            while self.pipeline.status.value == "running":
                metrics = self.collect_metrics()
                if metrics:
                    self.print_metrics(metrics)
                    self.metrics_history.append(metrics)
                
                import time
                time.sleep(self.interval)
        
        monitor_thread = threading.Thread(
            target=monitor_loop,
            name="StreamingMonitor",
            daemon=True
        )
        monitor_thread.start()
        logger.info("Monitoring started")


# ==================== Main Pipeline ====================

def create_spark_session(config: ProductionConfig) -> SparkSession:
    """Create and configure Spark session"""
    logger.info("Creating Spark session")
    
    return SparkSession.builder \
        .appName("KafkaOracleProduction") \
        .master("spark://master:7077") \
        .config("spark.driver.memory", config.SPARK_DRIVER_MEMORY) \
        .config("spark.executor.memory", config.SPARK_EXECUTOR_MEMORY) \
        .config("spark.executor.cores", "2") \
        .config("spark.sql.shuffle.partitions", config.SPARK_PARTITIONS) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.skewJoin.enabled", "true") \
        .config("spark.jars.packages", 
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()


def run_production_pipeline(config: ProductionConfig = None) -> None:
    """Run the complete production pipeline"""
    
    if config is None:
        config = ProductionConfig.from_env()
    
    logger.info("Starting Kafka to Oracle Streaming Pipeline")
    logger.info(f"Kafka: {config.KAFKA_BROKERS}")
    logger.info(f"Oracle: {config.ORACLE_HOST}:{config.ORACLE_PORT}/{config.ORACLE_SERVICE}")
    
    # Create Spark session
    spark = create_spark_session(config)
    
    try:
        # Configure Kafka
        kafka_config = KafkaConfig(
            bootstrap_servers=config.KAFKA_BROKERS,
            topic=config.KAFKA_TOPICS,
            group_id=config.KAFKA_GROUP,
            starting_offsets=config.KAFKA_START_OFFSET
        )
        
        # Configure Oracle
        oracle_config = OracleConfig(
            host=config.ORACLE_HOST,
            port=config.ORACLE_PORT,
            service_name=config.ORACLE_SERVICE,
            user=config.ORACLE_USER,
            password=config.ORACLE_PASSWORD
        )
        
        # Create pipeline
        pipeline = KafkaOracleStreamingPipeline(
            spark=spark,
            kafka_config=kafka_config,
            oracle_config=oracle_config,
            app_name="KafkaOracleProduction"
        )
        
        # Enable fault tolerance
        pipeline.enable_fault_tolerance(
            checkpoint_dir=config.CHECKPOINT_DIR,
            log_dir=f"{config.CHECKPOINT_DIR}/logs"
        )
        
        logger.info("Pipeline initialized successfully")
        
        # ========== Pipeline Steps ==========
        
        # Step 1: Read from Kafka
        logger.info("Step 1: Reading from Kafka")
        df_orders = pipeline.read_kafka_stream(schema=Schemas.order_schema())
        
        # Step 2: Transform
        logger.info("Step 2: Transforming data")
        df_transformed = pipeline.apply_transformation(df_orders, transform_order_data)
        
        # Step 3: Add metadata
        logger.info("Step 3: Adding metadata")
        df_with_metadata = pipeline.add_processing_metadata(df_transformed)
        
        # Step 4: Apply quality checks
        logger.info("Step 4: Applying quality checks")
        quality_rules = get_quality_rules()
        df_quality = pipeline.add_data_quality_checks(df_with_metadata, quality_rules)
        
        # Step 5: Split good and bad records
        logger.info("Step 5: Filtering records")
        df_good = df_quality.filter(
            col("quality_valid_order_id") &
            col("quality_valid_customer_id") &
            col("quality_valid_amount") &
            col("quality_valid_status") &
            col("quality_valid_date_format")
        )
        
        df_bad = df_quality.filter(
            ~col("quality_valid_order_id") |
            ~col("quality_valid_customer_id") |
            ~col("quality_valid_amount") |
            ~col("quality_valid_status") |
            ~col("quality_valid_date_format")
        )
        
        # Step 6: Write good records
        logger.info("Step 6: Writing to Oracle (valid records)")
        query_good = pipeline.write_to_oracle(
            df=df_good,
            table_name="orders_processed",
            mode="append",
            trigger_interval=config.BATCH_INTERVAL,
            checkpoint_location=f"{config.CHECKPOINT_DIR}/orders_processed"
        )
        
        # Step 7: Write bad records to error table
        logger.info("Step 7: Writing to Oracle (invalid records)")
        query_bad = pipeline.write_to_oracle(
            df=df_bad,
            table_name="orders_errors",
            mode="append",
            trigger_interval=config.BATCH_INTERVAL,
            checkpoint_location=f"{config.CHECKPOINT_DIR}/orders_errors"
        )
        
        # Step 8: Windowed aggregations
        logger.info("Step 8: Computing aggregations")
        df_windowed = pipeline.apply_windowing(
            df=df_good,
            timestamp_col="timestamp",
            window_duration="1 hour"
        )
        
        df_hourly_metrics = df_windowed.groupBy("time_window").agg(
            count("order_id").alias("order_count"),
            spark_sum("amount_usd").alias("total_amount"),
            avg("amount_usd").alias("avg_amount"),
            count(when(col("high_value"), 1)).alias("high_value_count")
        ).select(
            col("time_window.start").alias("window_start"),
            col("time_window.end").alias("window_end"),
            col("order_count"),
            col("total_amount"),
            col("avg_amount"),
            col("high_value_count")
        )
        
        query_metrics = pipeline.write_to_oracle(
            df=df_hourly_metrics,
            table_name="order_metrics_hourly",
            mode="complete",
            trigger_interval=config.BATCH_INTERVAL,
            checkpoint_location=f"{config.CHECKPOINT_DIR}/order_metrics_hourly"
        )
        
        logger.info("All streaming queries started")
        
        # ========== Monitoring ==========
        
        monitor = StreamingMonitor(pipeline, interval=config.MONITORING_INTERVAL)
        monitor.start_monitoring()
        
        logger.info("Pipeline running. Press Ctrl+C to stop.")
        
        # Wait for all queries to complete
        pipeline.wait_for_termination()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        pipeline.stop_all_streams()
        logger.info("Streams stopped successfully")
        
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}", exc_info=True)
        pipeline.stop_all_streams()
        raise
        
    finally:
        spark.stop()
        logger.info("Spark session closed")


# ==================== Entry Point ====================

if __name__ == "__main__":
    """
    Production Kafka to Oracle Streaming Pipeline
    
    Environment Variables:
    - KAFKA_BROKERS: Kafka broker addresses (default: localhost:9092)
    - ORACLE_HOST: Oracle host (default: localhost)
    - ORACLE_PASSWORD: Oracle password (required)
    
    Usage:
        python kafka_oracle_production.py
    
    Docker:
        docker run -e KAFKA_BROKERS=kafka:9092 \
                   -e ORACLE_HOST=oracle-db \
                   -e ORACLE_PASSWORD=secret \
                   kafka-oracle-streaming:latest
    """
    
    try:
        run_production_pipeline()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
