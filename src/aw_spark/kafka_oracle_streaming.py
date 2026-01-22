"""
Kafka to Oracle Streaming Pipeline

This module provides functionality to:
- Stream data from Kafka topics
- Process streaming data with Spark
- Write processed data to Oracle database
- Handle schema evolution and data validation
- Monitor streaming metrics
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import time
from dataclasses import dataclass
from enum import Enum

from pyspark.sql import SparkSession, DataFrame, DataFrameWriter
from pyspark.sql.functions import (
    col, from_json, to_json, struct, 
    current_timestamp, window, count, explode,
    to_date, year, month, day
)
from pyspark.sql.streaming import StreamingQuery
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, TimestampType

try:
    import oracledb as oracle_module
except ImportError:
    try:
        import cx_Oracle as oracle_module
    except ImportError:
        oracle_module = None

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class StreamingJobStatus(Enum):
    """Status of streaming job"""
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class KafkaConfig:
    """Kafka configuration"""
    bootstrap_servers: str
    topic: str
    group_id: str
    starting_offsets: str = "earliest"
    max_poll_records: int = 500
    session_timeout_ms: int = 30000
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        return {
            "kafka.bootstrap.servers": self.bootstrap_servers,
            "subscribe": self.topic,
            "group.id": self.group_id,
            "startingOffsets": self.starting_offsets,
            "maxOffsetsPerTrigger": str(self.max_poll_records),
            "sessionTimeoutMs": str(self.session_timeout_ms)
        }


@dataclass
class OracleConfig:
    """Oracle database configuration"""
    host: str
    port: int
    service_name: str
    user: str
    password: str
    
    def get_connection_string(self) -> str:
        """Get Oracle connection string"""
        return f"oracle://{self.user}:{self.password}@{self.host}:{self.port}/{self.service_name}"
    
    def get_jdbc_url(self) -> str:
        """Get JDBC URL for Spark"""
        return f"jdbc:oracle:thin:@{self.host}:{self.port}/{self.service_name}"


class KafkaOracleStreamingPipeline:
    """
    Main class for Kafka to Oracle streaming pipeline
    """

    def __init__(
        self,
        spark: SparkSession,
        kafka_config: KafkaConfig,
        oracle_config: OracleConfig,
        app_name: str = "Kafka-Oracle-Pipeline"
    ):
        """
        Initialize streaming pipeline
        
        Args:
            spark: SparkSession instance
            kafka_config: Kafka configuration
            oracle_config: Oracle database configuration
            app_name: Application name
        """
        self.spark = spark
        self.kafka_config = kafka_config
        self.oracle_config = oracle_config
        self.app_name = app_name
        
        # Configure Spark for streaming
        self._configure_spark()
        
        self.streaming_queries: Dict[str, StreamingQuery] = {}
        self.metrics: Dict[str, Any] = {}
        self.status = StreamingJobStatus.CREATED
        
        logger.info(f"Initialized Kafka-Oracle Streaming Pipeline: {app_name}")

    def _configure_spark(self) -> None:
        """Configure Spark for streaming"""
        try:
            self.spark.conf.set("spark.sql.streaming.checkpointLocation", "/tmp/streaming-checkpoint")
            self.spark.conf.set("spark.sql.streaming.schemaInference", "true")
            self.spark.conf.set("spark.sql.adaptive.enabled", "true")
            logger.info("Spark configured for streaming")
        except Exception as e:
            logger.error(f"Error configuring Spark: {str(e)}")
            raise

    # ==================== Kafka Read Operations ====================

    def read_kafka_stream(
        self,
        schema: Optional[StructType] = None
    ) -> DataFrame:
        """
        Read streaming data from Kafka
        
        Args:
            schema: Optional schema for JSON parsing
            
        Returns:
            DataFrame: Streaming DataFrame from Kafka
        """
        try:
            logger.info(f"Reading from Kafka topic: {self.kafka_config.topic}")
            
            df = self.spark.readStream \
                .format("kafka") \
                .options(**self.kafka_config.to_dict()) \
                .load()
            
            # Parse JSON value if schema provided
            if schema:
                df = df.select(
                    from_json(col("value").cast("string"), schema).alias("data"),
                    col("timestamp"),
                    col("partition"),
                    col("offset")
                ).select("data.*", "timestamp", "partition", "offset")
            else:
                # Parse as generic JSON
                df = df.select(
                    from_json(col("value").cast("string"), "MAP<STRING, STRING>").alias("data"),
                    col("timestamp"),
                    col("partition"),
                    col("offset")
                )
            
            logger.info("Successfully created Kafka stream")
            return df
        except Exception as e:
            logger.error(f"Error reading from Kafka: {str(e)}")
            raise

    # ==================== Stream Processing ====================

    def apply_transformation(
        self,
        df: DataFrame,
        transformation_func: Callable[[DataFrame], DataFrame]
    ) -> DataFrame:
        """
        Apply custom transformation to stream
        
        Args:
            df: Input streaming DataFrame
            transformation_func: Function to transform DataFrame
            
        Returns:
            DataFrame: Transformed streaming DataFrame
        """
        try:
            logger.info("Applying transformation to stream")
            result_df = transformation_func(df)
            return result_df
        except Exception as e:
            logger.error(f"Error applying transformation: {str(e)}")
            raise

    def add_processing_metadata(self, df: DataFrame) -> DataFrame:
        """
        Add metadata columns for processing
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame: DataFrame with metadata
        """
        try:
            df = df.withColumn("processed_at", current_timestamp()) \
                .withColumn("pipeline_name", df.sparkSession.sparkContext.appName) \
                .withColumn("processing_date", to_date(current_timestamp()))
            
            logger.info("Added processing metadata")
            return df
        except Exception as e:
            logger.error(f"Error adding metadata: {str(e)}")
            raise

    def apply_windowing(
        self,
        df: DataFrame,
        timestamp_col: str,
        window_duration: str,
        slide_duration: Optional[str] = None
    ) -> DataFrame:
        """
        Apply time windowing to stream
        
        Args:
            df: Input streaming DataFrame
            timestamp_col: Name of timestamp column
            window_duration: Window duration (e.g., "10 minutes")
            slide_duration: Slide duration for sliding windows
            
        Returns:
            DataFrame: Windowed streaming DataFrame
        """
        try:
            logger.info(f"Applying window: {window_duration}")
            
            if slide_duration:
                df = df.withColumn(
                    "time_window",
                    window(col(timestamp_col), window_duration, slide_duration)
                )
            else:
                df = df.withColumn(
                    "time_window",
                    window(col(timestamp_col), window_duration)
                )
            
            return df
        except Exception as e:
            logger.error(f"Error applying windowing: {str(e)}")
            raise

    def filter_stream(
        self,
        df: DataFrame,
        condition: str
    ) -> DataFrame:
        """
        Filter streaming data
        
        Args:
            df: Input streaming DataFrame
            condition: Filter condition
            
        Returns:
            DataFrame: Filtered streaming DataFrame
        """
        try:
            logger.info(f"Filtering stream with condition: {condition}")
            result_df = df.filter(condition)
            return result_df
        except Exception as e:
            logger.error(f"Error filtering stream: {str(e)}")
            raise

    def deduplicate_stream(
        self,
        df: DataFrame,
        subset: List[str],
        within_window: Optional[str] = None
    ) -> DataFrame:
        """
        Remove duplicates from stream
        
        Args:
            df: Input streaming DataFrame
            subset: Columns to consider for duplicates
            within_window: Optional time window for deduplication
            
        Returns:
            DataFrame: Deduplicated streaming DataFrame
        """
        try:
            logger.info(f"Deduplicating stream on columns: {subset}")
            
            if within_window:
                df = df.withWatermark("timestamp", within_window) \
                    .dropDuplicates(subset)
            else:
                df = df.dropDuplicates(subset)
            
            return df
        except Exception as e:
            logger.error(f"Error deduplicating stream: {str(e)}")
            raise

    # ==================== Oracle Write Operations ====================

    def write_to_oracle(
        self,
        df: DataFrame,
        table_name: str,
        mode: str = "append",
        checkpoint_location: Optional[str] = None,
        trigger_interval: str = "10 seconds"
    ) -> StreamingQuery:
        """
        Write streaming DataFrame to Oracle
        
        Args:
            df: Input streaming DataFrame
            table_name: Target Oracle table name
            mode: Write mode (append, complete, update)
            checkpoint_location: Checkpoint directory for fault tolerance
            trigger_interval: Micro-batch trigger interval
            
        Returns:
            StreamingQuery: Query handle for monitoring
        """
        try:
            logger.info(f"Writing stream to Oracle table: {table_name}")
            
            checkpoint = checkpoint_location or f"/tmp/checkpoint/{table_name}"
            
            # Create write function
            def write_batch(batch_df: DataFrame, batch_id: int) -> None:
                """Write batch to Oracle"""
                try:
                    self._write_batch_to_oracle(batch_df, table_name)
                    logger.info(f"Batch {batch_id} written to Oracle successfully")
                except Exception as e:
                    logger.error(f"Error writing batch {batch_id} to Oracle: {str(e)}")
                    raise
            
            # Start streaming query
            query = df.writeStream \
                .foreachBatch(write_batch) \
                .option("checkpointLocation", checkpoint) \
                .trigger(processingTime=trigger_interval) \
                .start()
            
            self.streaming_queries[table_name] = query
            self.status = StreamingJobStatus.RUNNING
            logger.info(f"Streaming query started for {table_name}")
            
            return query
        except Exception as e:
            logger.error(f"Error setting up Oracle write stream: {str(e)}")
            self.status = StreamingJobStatus.FAILED
            raise

    def _write_batch_to_oracle(self, df: DataFrame, table_name: str) -> None:
        """
        Write a batch of data to Oracle
        
        Args:
            df: Batch DataFrame
            table_name: Target table name
        """
        try:
            # Convert to Pandas for writing
            pandas_df = df.toPandas()
            
            if pandas_df.empty:
                logger.debug(f"Empty batch for {table_name}")
                return
            
            # Create SQLAlchemy engine
            engine = create_engine(
                self.oracle_config.get_connection_string()
            )
            
            # Write to Oracle
            pandas_df.to_sql(
                table_name.lower(),
                con=engine,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000
            )
            
            engine.dispose()
            logger.info(f"Written {len(pandas_df)} rows to {table_name}")
        except Exception as e:
            logger.error(f"Error writing batch to Oracle: {str(e)}")
            raise

    def write_to_oracle_jdbc(
        self,
        df: DataFrame,
        table_name: str,
        mode: str = "append"
    ) -> None:
        """
        Write DataFrame to Oracle using JDBC (for batch operations)
        
        Args:
            df: Input DataFrame
            table_name: Target table name
            mode: Write mode (overwrite, append, ignore, error)
        """
        try:
            logger.info(f"Writing to Oracle via JDBC: {table_name}")
            
            df.write \
                .format("jdbc") \
                .mode(mode) \
                .option("url", self.oracle_config.get_jdbc_url()) \
                .option("dbtable", table_name) \
                .option("user", self.oracle_config.user) \
                .option("password", self.oracle_config.password) \
                .option("driver", "oracle.jdbc.driver.OracleDriver") \
                .option("numPartitions", "4") \
                .save()
            
            logger.info(f"Successfully written to {table_name}")
        except Exception as e:
            logger.error(f"Error writing to Oracle via JDBC: {str(e)}")
            raise

    # ==================== Data Validation ====================

    def validate_stream_schema(
        self,
        df: DataFrame,
        expected_columns: Dict[str, str]
    ) -> tuple:
        """
        Validate streaming DataFrame schema
        
        Args:
            df: Input streaming DataFrame
            expected_columns: Dict mapping column names to expected types
            
        Returns:
            tuple: (is_valid, errors_list)
        """
        try:
            logger.info("Validating stream schema")
            errors = []
            
            actual_schema = {field.name: field.dataType.typeName() 
                           for field in df.schema.fields}
            
            for col_name, expected_type in expected_columns.items():
                if col_name not in actual_schema:
                    errors.append(f"Missing column: {col_name}")
                elif actual_schema[col_name] != expected_type:
                    errors.append(
                        f"Column {col_name}: expected {expected_type}, "
                        f"got {actual_schema[col_name]}"
                    )
            
            is_valid = len(errors) == 0
            logger.info(f"Schema validation: {'PASSED' if is_valid else 'FAILED'}")
            return is_valid, errors
        except Exception as e:
            logger.error(f"Error validating schema: {str(e)}")
            raise

    def add_data_quality_checks(
        self,
        df: DataFrame,
        quality_rules: Dict[str, Callable]
    ) -> DataFrame:
        """
        Add data quality validation columns
        
        Args:
            df: Input streaming DataFrame
            quality_rules: Dict mapping rule names to validation functions
            
        Returns:
            DataFrame: DataFrame with quality check columns
        """
        try:
            logger.info("Adding data quality checks")
            
            for rule_name, rule_func in quality_rules.items():
                df = df.withColumn(f"quality_{rule_name}", rule_func(df))
            
            return df
        except Exception as e:
            logger.error(f"Error adding quality checks: {str(e)}")
            raise

    # ==================== Monitoring ====================

    def get_stream_progress(self, stream_name: str) -> Dict[str, Any]:
        """
        Get progress information for a streaming query
        
        Args:
            stream_name: Name of the streaming query
            
        Returns:
            Dict: Progress information
        """
        try:
            if stream_name not in self.streaming_queries:
                logger.warning(f"Stream {stream_name} not found")
                return {}
            
            query = self.streaming_queries[stream_name]
            progress = query.lastProgress
            
            if progress:
                return {
                    "id": progress.get("id"),
                    "runId": progress.get("runId"),
                    "name": progress.get("name"),
                    "timestamp": progress.get("timestamp"),
                    "inputRowsPerSecond": progress.get("inputRowsPerSecond"),
                    "processedRowsPerSecond": progress.get("processedRowsPerSecond"),
                    "numInputPartitions": progress.get("numInputPartitions"),
                    "numInputRows": progress.get("numInputRows"),
                    "numProcessedRows": progress.get("numProcessedRows"),
                    "batchDuration": progress.get("durationMs", {}).get("total")
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting stream progress: {str(e)}")
            return {}

    def monitor_streams(self, interval: int = 30) -> None:
        """
        Monitor all active streams
        
        Args:
            interval: Monitoring interval in seconds
        """
        try:
            logger.info(f"Starting stream monitoring (interval: {interval}s)")
            
            while self.status == StreamingJobStatus.RUNNING:
                for stream_name, query in self.streaming_queries.items():
                    if query.isActive:
                        progress = self.get_stream_progress(stream_name)
                        logger.info(f"Stream {stream_name}: {progress}")
                    else:
                        logger.warning(f"Stream {stream_name} is not active")
                
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error during monitoring: {str(e)}")

    # ==================== Query Management ====================

    def stop_stream(self, stream_name: str) -> None:
        """
        Stop a streaming query
        
        Args:
            stream_name: Name of the streaming query
        """
        try:
            if stream_name in self.streaming_queries:
                query = self.streaming_queries[stream_name]
                query.stop()
                logger.info(f"Stream {stream_name} stopped")
        except Exception as e:
            logger.error(f"Error stopping stream: {str(e)}")

    def stop_all_streams(self) -> None:
        """Stop all active streaming queries"""
        try:
            logger.info("Stopping all streams")
            for stream_name in list(self.streaming_queries.keys()):
                self.stop_stream(stream_name)
            
            self.status = StreamingJobStatus.STOPPED
            logger.info("All streams stopped")
        except Exception as e:
            logger.error(f"Error stopping all streams: {str(e)}")

    def wait_for_termination(self, timeout: Optional[int] = None) -> None:
        """
        Wait for all streaming queries to terminate
        
        Args:
            timeout: Timeout in seconds (None for indefinite)
        """
        try:
            logger.info("Waiting for stream termination")
            for query in self.streaming_queries.values():
                query.awaitTermination(timeout)
        except Exception as e:
            logger.error(f"Error waiting for termination: {str(e)}")

    # ==================== Recovery & Checkpointing ====================

    def enable_fault_tolerance(
        self,
        checkpoint_dir: str,
        log_dir: Optional[str] = None
    ) -> None:
        """
        Enable fault tolerance with checkpointing
        
        Args:
            checkpoint_dir: Directory for checkpoints
            log_dir: Directory for logs
        """
        try:
            logger.info(f"Enabling fault tolerance with checkpoint dir: {checkpoint_dir}")
            self.spark.conf.set("spark.sql.streaming.checkpointLocation", checkpoint_dir)
            
            if log_dir:
                self.spark.conf.set("spark.eventLog.dir", log_dir)
            
            logger.info("Fault tolerance enabled")
        except Exception as e:
            logger.error(f"Error enabling fault tolerance: {str(e)}")
            raise

    # ==================== Batch Operations ====================

    def read_oracle_table(self, table_name: str) -> DataFrame:
        """
        Read data from Oracle table
        
        Args:
            table_name: Oracle table name
            
        Returns:
            DataFrame: Read DataFrame
        """
        try:
            logger.info(f"Reading from Oracle table: {table_name}")
            
            df = self.spark.read \
                .format("jdbc") \
                .option("url", self.oracle_config.get_jdbc_url()) \
                .option("dbtable", table_name) \
                .option("user", self.oracle_config.user) \
                .option("password", self.oracle_config.password) \
                .option("driver", "oracle.jdbc.driver.OracleDriver") \
                .option("numPartitions", "4") \
                .load()
            
            logger.info(f"Read {df.count()} rows from {table_name}")
            return df
        except Exception as e:
            logger.error(f"Error reading from Oracle: {str(e)}")
            raise

    # ==================== Utilities ====================

    def create_oracle_table(
        self,
        table_name: str,
        schema_dict: Dict[str, str],
        primary_keys: Optional[List[str]] = None
    ) -> None:
        """
        Create table in Oracle
        
        Args:
            table_name: Table name to create
            schema_dict: Dict mapping column names to SQL types
            primary_keys: List of primary key columns
        """
        try:
            logger.info(f"Creating Oracle table: {table_name}")
            
            # Build column definitions
            columns = []
            for col_name, col_type in schema_dict.items():
                columns.append(f"{col_name.upper()} {col_type}")
            
            # Add primary key constraint
            if primary_keys:
                pk_constraint = f"PRIMARY KEY ({', '.join(primary_keys)})"
                columns.append(pk_constraint)
            
            # Build CREATE TABLE statement
            create_stmt = f"CREATE TABLE {table_name.upper()} ({', '.join(columns)})"
            
            # Execute
            engine = create_engine(
                self.oracle_config.get_connection_string()
            )
            with engine.connect() as conn:
                conn.execute(text(create_stmt))
                conn.commit()
            
            engine.dispose()
            logger.info(f"Table {table_name} created successfully")
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            raise

    def get_stream_status(self) -> Dict[str, Any]:
        """
        Get status of all streams
        
        Returns:
            Dict: Status information
        """
        try:
            status = {
                "pipeline_status": self.status.value,
                "streams": {}
            }
            
            for stream_name, query in self.streaming_queries.items():
                status["streams"][stream_name] = {
                    "active": query.isActive,
                    "progress": self.get_stream_progress(stream_name)
                }
            
            return status
        except Exception as e:
            logger.error(f"Error getting stream status: {str(e)}")
            return {}
