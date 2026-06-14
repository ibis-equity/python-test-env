# Kafka to Oracle Streaming Pipeline Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Usage Examples](#usage-examples)
8. [Data Quality & Validation](#data-quality--validation)
9. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
10. [Performance Optimization](#performance-optimization)
11. [Deployment Guide](#deployment-guide)

---

## Overview

The Kafka to Oracle Streaming Pipeline provides a production-ready framework for:

- **Real-time Data Streaming**: Consume messages from Apache Kafka topics
- **Data Processing**: Transform, validate, and enrich data in real-time using Spark
- **Database Integration**: Write streaming data directly to Oracle Database
- **Fault Tolerance**: Automatic checkpointing and recovery mechanisms
- **Monitoring**: Built-in stream health monitoring and metrics
- **Schema Management**: Handle schema evolution and validation

### Key Features

- ✅ **Kafka Consumer**: Efficiently consume from Kafka topics with configurable offsets
- ✅ **Spark Streaming**: Micro-batch and continuous processing models
- ✅ **Oracle Integration**: JDBC and SQLAlchemy-based writes with automatic batching
- ✅ **Data Quality**: Validation rules, deduplication, and null handling
- ✅ **Time Windowing**: Tumbling, sliding, and session windows
- ✅ **Exactly-Once Semantics**: Transaction semantics with checkpointing
- ✅ **Schema Evolution**: Handle schema changes gracefully
- ✅ **Multi-Topic Support**: Stream from multiple Kafka topics simultaneously

---

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│  Kafka Topics   │
│  (orders, etc)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  Spark Streaming            │
│  - Read Stream              │
│  - Parse/Deserialize        │
│  - Validate Schema          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Data Processing            │
│  - Transform                │
│  - Window/Aggregate         │
│  - Add Metadata             │
│  - Quality Checks           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Oracle Database            │
│  - Write Stream             │
│  - Checkpoint Store         │
│  - Data Persistence         │
└─────────────────────────────┘
```

### Processing Flow

1. **Ingestion**: Kafka consumer reads from topics
2. **Parsing**: JSON/CSV messages deserialized using provided schema
3. **Processing**: Spark applies transformations in micro-batches
4. **Validation**: Data quality checks applied before write
5. **Persistence**: Batches written to Oracle with checkpoint tracking
6. **Recovery**: Checkpoints enable resume from failure points

---

## Core Components

### 1. KafkaOracleStreamingPipeline (Main Class)

**Purpose**: Orchestrates the complete streaming pipeline

**Key Attributes**:
- `spark`: SparkSession instance
- `kafka_config`: Kafka connection configuration
- `oracle_config`: Oracle database configuration
- `streaming_queries`: Dict of active StreamingQuery objects
- `status`: Current pipeline status

**Responsibilities**:
- Initialize Spark streaming context
- Manage Kafka consumer
- Coordinate transformations
- Handle writes to Oracle
- Manage lifecycle (start, stop, monitor)

### 2. KafkaConfig (Configuration Class)

**Purpose**: Encapsulates Kafka connection parameters

**Parameters**:
```python
KafkaConfig(
    bootstrap_servers="localhost:9092",        # Kafka broker addresses
    topic="orders",                             # Topic to consume
    group_id="oracle-consumer",                # Consumer group
    starting_offsets="earliest",               # Start from beginning/latest
    max_poll_records=500,                      # Records per batch
    session_timeout_ms=30000                   # Session timeout
)
```

### 3. OracleConfig (Configuration Class)

**Purpose**: Encapsulates Oracle database connection parameters

**Parameters**:
```python
OracleConfig(
    host="localhost",                          # Oracle host
    port=1521,                                 # Oracle port
    service_name="XE",                         # Oracle service
    user="system",                             # Database user
    password="oracle"                          # Database password
)
```

**Methods**:
- `get_connection_string()`: Returns SQLAlchemy connection string
- `get_jdbc_url()`: Returns JDBC URL for Spark

### 4. StreamingJobStatus (Enum)

**Purpose**: Tracks pipeline state

**States**:
- `CREATED`: Pipeline initialized
- `RUNNING`: Streams actively processing
- `STOPPED`: Streams halted
- `FAILED`: Stream encountered error
- `COMPLETED`: All streams finished

---

## Installation & Setup

### Prerequisites

- Java 8+ (for Spark and Kafka)
- Python 3.7+
- Spark 3.5+
- Apache Kafka 2.8+
- Oracle Database 11g+ or Oracle Express Edition (XE)

### Required Python Packages

```bash
pip install pyspark==3.5.0
pip install kafka-python==2.0.2
pip install cx-Oracle==8.3.0
pip install sqlalchemy==2.0.0
pip install pandas==2.0.0
```

### Add to requirements.txt

```
pyspark==3.5.0
kafka-python==2.0.2
cx-Oracle==8.3.0
sqlalchemy==2.0.0
pandas==2.0.0
pyarrow==12.0.0
```

### Spark Initialization

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("KafkaOracleStreaming") \
    .master("local[*]") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()
```

---

## Configuration

### Kafka Configuration

**Topic Setup**:
```bash
# Create topic in Kafka
kafka-topics.sh --create \
  --topic orders \
  --partitions 3 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092

# Verify topic
kafka-topics.sh --list --bootstrap-server localhost:9092
```

**Message Format** (JSON):
```json
{
  "order_id": "ORD-001",
  "customer_id": "CUST-123",
  "amount": 1500.50,
  "product_category": "Electronics",
  "order_date": "2024-01-19"
}
```

### Oracle Configuration

**User Setup**:
```sql
-- Create application user
CREATE USER kafka_user IDENTIFIED BY kafka_password;
GRANT CONNECT, RESOURCE TO kafka_user;

-- Create table
CREATE TABLE kafka_user.orders_stream (
    order_id VARCHAR2(50),
    customer_id VARCHAR2(50),
    amount NUMBER(10,2),
    product_category VARCHAR2(100),
    order_date VARCHAR2(20),
    processed_at TIMESTAMP,
    pipeline_name VARCHAR2(100),
    processing_date DATE
);
```

**JDBC Driver Setup**:
```
1. Download Oracle JDBC driver (ojdbc8.jar)
2. Add to Spark classpath or use:
   --jars /path/to/ojdbc8.jar
```

---

## API Reference

### Stream Reading Operations

#### `read_kafka_stream(schema=None)`

**Description**: Read streaming data from Kafka topic

**Parameters**:
- `schema` (StructType, optional): Schema for JSON message parsing

**Returns**: 
- DataFrame: Streaming DataFrame

**Example**:
```python
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

schema = StructType([
    StructField("order_id", StringType()),
    StructField("amount", DoubleType())
])

df = pipeline.read_kafka_stream(schema=schema)
```

---

### Stream Processing Operations

#### `apply_transformation(df, transformation_func)`

**Description**: Apply custom transformation to stream

**Parameters**:
- `df` (DataFrame): Streaming DataFrame
- `transformation_func` (Callable): Function returning transformed DataFrame

**Returns**: 
- DataFrame: Transformed streaming DataFrame

**Example**:
```python
def transform_func(df):
    return df.withColumn("amount_usd", col("amount") * 1.1)

df_transformed = pipeline.apply_transformation(df, transform_func)
```

---

#### `add_processing_metadata(df)`

**Description**: Add metadata columns to DataFrame

**Columns Added**:
- `processed_at`: Current timestamp
- `pipeline_name`: Application name
- `processing_date`: Date of processing

**Example**:
```python
df_with_metadata = pipeline.add_processing_metadata(df)
```

---

#### `apply_windowing(df, timestamp_col, window_duration, slide_duration=None)`

**Description**: Apply time-based windowing

**Parameters**:
- `df` (DataFrame): Input DataFrame
- `timestamp_col` (str): Timestamp column name
- `window_duration` (str): Window size (e.g., "10 minutes")
- `slide_duration` (str, optional): Sliding duration for sliding windows

**Window Durations**:
- `"10 seconds"`, `"1 minute"`, `"5 minutes"`, `"1 hour"`, `"1 day"`

**Example**:
```python
# Tumbling window (5 minutes)
df_windowed = pipeline.apply_windowing(
    df, "timestamp", "5 minutes"
)

# Sliding window (5 minutes, 1 minute slide)
df_sliding = pipeline.apply_windowing(
    df, "timestamp", "5 minutes", "1 minute"
)
```

---

#### `filter_stream(df, condition)`

**Description**: Filter streaming records

**Parameters**:
- `df` (DataFrame): Input DataFrame
- `condition` (str): SQL filter condition

**Example**:
```python
df_filtered = pipeline.filter_stream(df, "amount > 1000")
```

---

#### `deduplicate_stream(df, subset, within_window=None)`

**Description**: Remove duplicate records

**Parameters**:
- `df` (DataFrame): Input DataFrame
- `subset` (List[str]): Columns to check for duplicates
- `within_window` (str, optional): Time window for watermarking

**Example**:
```python
df_dedup = pipeline.deduplicate_stream(
    df, 
    subset=["transaction_id"],
    within_window="1 hour"
)
```

---

### Stream Writing Operations

#### `write_to_oracle(df, table_name, mode="append", checkpoint_location=None, trigger_interval="10 seconds")`

**Description**: Write streaming DataFrame to Oracle

**Parameters**:
- `df` (DataFrame): Streaming DataFrame
- `table_name` (str): Target Oracle table
- `mode` (str): Write mode - `"append"`, `"complete"`, `"update"`
- `checkpoint_location` (str, optional): Directory for fault tolerance
- `trigger_interval` (str): Micro-batch interval

**Returns**: 
- StreamingQuery: Query handle

**Write Modes**:
- `"append"`: Add new rows only
- `"complete"`: Write entire result set
- `"update"`: Update modified rows

**Example**:
```python
query = pipeline.write_to_oracle(
    df=df_processed,
    table_name="orders_processed",
    mode="append",
    trigger_interval="30 seconds"
)
```

---

#### `write_to_oracle_jdbc(df, table_name, mode="append")`

**Description**: Batch write using JDBC (non-streaming)

**Parameters**:
- `df` (DataFrame): DataFrame to write
- `table_name` (str): Target table
- `mode` (str): `"overwrite"`, `"append"`, `"ignore"`, `"error"`

**Example**:
```python
pipeline.write_to_oracle_jdbc(
    df_batch,
    "orders_backup",
    mode="overwrite"
)
```

---

### Data Validation Operations

#### `validate_stream_schema(df, expected_columns)`

**Description**: Validate DataFrame schema

**Parameters**:
- `df` (DataFrame): DataFrame to validate
- `expected_columns` (Dict[str, str]): Map of column names to types

**Returns**: 
- tuple: (is_valid: bool, errors: List[str])

**Example**:
```python
expected = {
    "order_id": "string",
    "amount": "double"
}

is_valid, errors = pipeline.validate_stream_schema(df, expected)
if not is_valid:
    print(f"Schema errors: {errors}")
```

---

#### `add_data_quality_checks(df, quality_rules)`

**Description**: Add quality check columns

**Parameters**:
- `df` (DataFrame): Input DataFrame
- `quality_rules` (Dict[str, Callable]): Map of rule names to validation functions

**Returns**: 
- DataFrame: DataFrame with quality columns

**Example**:
```python
from pyspark.sql.functions import col

rules = {
    "valid_amount": lambda df: (col("amount") > 0) & (col("amount") < 100000),
    "valid_email": lambda df: col("email").rlike("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
}

df_quality = pipeline.add_data_quality_checks(df, rules)

# Filter good records
df_good = df_quality.filter(
    col("quality_valid_amount") & col("quality_valid_email")
)
```

---

### Monitoring Operations

#### `get_stream_progress(stream_name)`

**Description**: Get streaming query progress

**Parameters**:
- `stream_name` (str): Name of the streaming query

**Returns**: 
- Dict: Progress information

**Progress Metrics**:
- `inputRowsPerSecond`: Input rate
- `processedRowsPerSecond`: Processing rate
- `numInputRows`: Total input rows
- `numProcessedRows`: Total processed rows
- `batchDuration`: Time to process batch

**Example**:
```python
progress = pipeline.get_stream_progress("orders_stream")
print(f"Input rate: {progress['inputRowsPerSecond']} rows/sec")
print(f"Processing rate: {progress['processedRowsPerSecond']} rows/sec")
```

---

#### `monitor_streams(interval=30)`

**Description**: Continuously monitor all streams

**Parameters**:
- `interval` (int): Monitoring interval in seconds

**Example**:
```python
# Run in background thread
import threading
monitor_thread = threading.Thread(
    target=pipeline.monitor_streams,
    kwargs={"interval": 60},
    daemon=True
)
monitor_thread.start()
```

---

#### `get_stream_status()`

**Description**: Get status of all active streams

**Returns**: 
- Dict: Status information for all streams

**Example**:
```python
status = pipeline.get_stream_status()
print(status)
# Output:
# {
#     "pipeline_status": "running",
#     "streams": {
#         "orders_stream": {"active": true, "progress": {...}}
#     }
# }
```

---

### Query Management Operations

#### `stop_stream(stream_name)`

**Description**: Stop a specific streaming query

**Parameters**:
- `stream_name` (str): Name of the streaming query

**Example**:
```python
pipeline.stop_stream("orders_stream")
```

---

#### `stop_all_streams()`

**Description**: Stop all active streaming queries

**Example**:
```python
pipeline.stop_all_streams()
```

---

#### `wait_for_termination(timeout=None)`

**Description**: Block until streams terminate

**Parameters**:
- `timeout` (int, optional): Timeout in seconds

**Example**:
```python
# Wait indefinitely
pipeline.wait_for_termination()

# Wait up to 3600 seconds
pipeline.wait_for_termination(timeout=3600)
```

---

### Recovery Operations

#### `enable_fault_tolerance(checkpoint_dir, log_dir=None)`

**Description**: Enable checkpointing for fault tolerance

**Parameters**:
- `checkpoint_dir` (str): Directory for checkpoints
- `log_dir` (str, optional): Directory for event logs

**Example**:
```python
pipeline.enable_fault_tolerance(
    checkpoint_dir="/data/kafka_checkpoints",
    log_dir="/var/log/spark_events"
)
```

---

### Batch Operations

#### `read_oracle_table(table_name)`

**Description**: Read existing Oracle table as batch

**Parameters**:
- `table_name` (str): Oracle table name

**Returns**: 
- DataFrame: Batch DataFrame

**Example**:
```python
df_historical = pipeline.read_oracle_table("orders_archive")
df_historical.show()
```

---

#### `create_oracle_table(table_name, schema_dict, primary_keys=None)`

**Description**: Create table in Oracle

**Parameters**:
- `table_name` (str): Table name
- `schema_dict` (Dict[str, str]): Column definitions
- `primary_keys` (List[str], optional): Primary key columns

**Example**:
```python
schema = {
    "order_id": "VARCHAR2(50)",
    "customer_id": "VARCHAR2(50)",
    "amount": "NUMBER(10,2)",
    "created_at": "TIMESTAMP"
}

pipeline.create_oracle_table(
    "orders_new",
    schema,
    primary_keys=["order_id"]
)
```

---

## Usage Examples

### Example 1: Basic Stream Read and Write

```python
from pyspark.sql import SparkSession
from kafka_oracle_streaming import (
    KafkaOracleStreamingPipeline,
    KafkaConfig,
    OracleConfig
)

# Initialize Spark
spark = SparkSession.builder \
    .appName("BasicStreaming") \
    .master("local[*]") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
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
df = pipeline.read_kafka_stream()

# Write to Oracle
query = pipeline.write_to_oracle(
    df=df,
    table_name="orders_stream"
)

# Wait for termination
query.awaitTermination()
```

---

### Example 2: Stream with Transformations

```python
from pyspark.sql.functions import col, regexp_extract
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# Define schema
schema = StructType([
    StructField("order_id", StringType()),
    StructField("customer_id", StringType()),
    StructField("amount", DoubleType()),
    StructField("order_date", StringType())
])

# Read with schema
df = pipeline.read_kafka_stream(schema=schema)

# Transform data
def transform_orders(df):
    return df \
        .withColumn("amount_usd", col("amount") * 1.1) \
        .withColumn("year", regexp_extract(col("order_date"), r"(\d{4})", 1)) \
        .withColumn("high_value", col("amount") > 1000)

df_transformed = pipeline.apply_transformation(df, transform_orders)

# Add metadata
df_with_metadata = pipeline.add_processing_metadata(df_transformed)

# Write to Oracle
query = pipeline.write_to_oracle(
    df=df_with_metadata,
    table_name="orders_processed"
)

query.awaitTermination()
```

---

### Example 3: Windowed Aggregations

```python
from pyspark.sql.functions import count, sum, avg, col

# Read stream
df = pipeline.read_kafka_stream(schema=schema)

# Apply 5-minute window
df_windowed = pipeline.apply_windowing(
    df=df,
    timestamp_col="timestamp",
    window_duration="5 minutes"
)

# Aggregate
df_agg = df_windowed.groupBy("time_window").agg(
    count("order_id").alias("order_count"),
    sum("amount").alias("total_amount"),
    avg("amount").alias("avg_amount")
).select(
    col("time_window.start").alias("window_start"),
    col("time_window.end").alias("window_end"),
    col("order_count"),
    col("total_amount"),
    col("avg_amount")
)

# Write aggregated results
query = pipeline.write_to_oracle(
    df=df_agg,
    table_name="order_metrics_5min"
)

query.awaitTermination()
```

---

### Example 4: Data Quality Checks

```python
from pyspark.sql.functions import col

# Read stream
df = pipeline.read_kafka_stream(schema=schema)

# Define quality rules
rules = {
    "valid_amount": lambda df: (col("amount") > 0) & (col("amount") < 100000),
    "valid_customer": lambda df: col("customer_id").isNotNull(),
    "valid_date": lambda df: col("order_date").isNotNull()
}

# Add quality checks
df_quality = pipeline.add_data_quality_checks(df, rules)

# Split good and bad records
df_good = df_quality.filter(
    col("quality_valid_amount") & 
    col("quality_valid_customer") & 
    col("quality_valid_date")
)

df_bad = df_quality.filter(
    ~col("quality_valid_amount") | 
    ~col("quality_valid_customer") | 
    ~col("quality_valid_date")
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

query_good.awaitTermination()
```

---

### Example 5: Deduplication

```python
# Read stream
df = pipeline.read_kafka_stream(schema=schema)

# Deduplicate on transaction_id within 1-hour window
df_dedup = pipeline.deduplicate_stream(
    df=df,
    subset=["transaction_id"],
    within_window="1 hour"
)

# Write deduplicated records
query = pipeline.write_to_oracle(
    df=df_dedup,
    table_name="transactions_deduplicated"
)

query.awaitTermination()
```

---

## Data Quality & Validation

### Schema Validation

```python
# Define expected schema
expected_columns = {
    "order_id": "string",
    "customer_id": "string",
    "amount": "double",
    "order_date": "string"
}

# Validate incoming stream
is_valid, errors = pipeline.validate_stream_schema(df, expected_columns)

if not is_valid:
    logger.error(f"Schema validation failed: {errors}")
    # Route to error queue
else:
    logger.info("Schema validation passed")
    # Proceed with processing
```

---

### Data Quality Rules

```python
from pyspark.sql.functions import col, length, regexp_extract

# Define comprehensive rules
quality_rules = {
    # Amount validations
    "amount_positive": lambda df: col("amount") > 0,
    "amount_reasonable": lambda df: col("amount") < 1000000,
    
    # ID validations
    "order_id_not_null": lambda df: col("order_id").isNotNull(),
    "order_id_length": lambda df: length(col("order_id")) > 0,
    
    # Email validations
    "email_format": lambda df: col("email").rlike(
        "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    ),
    
    # Date validations
    "date_valid": lambda df: regexp_extract(col("date"), r"^\d{4}-\d{2}-\d{2}$").isNotNull()
}

# Apply rules
df_quality = pipeline.add_data_quality_checks(df, quality_rules)

# Analyze quality metrics
quality_summary = df_quality.select([
    f"quality_{rule}" for rule in quality_rules.keys()
]).describe().show()
```

---

### Null Handling

```python
from pyspark.sql.functions import col, when

# Drop rows with nulls in critical columns
df_cleaned = df.dropna(
    subset=["order_id", "customer_id", "amount"]
)

# Fill nulls with defaults
df_filled = df.fillna({
    "product_category": "Unknown",
    "shipping_address": "Not Provided",
    "amount": 0.0
})

# Conditional fill
df_conditional = df.withColumn(
    "order_type",
    when(col("amount") > 1000, "Large").otherwise("Standard")
)
```

---

## Monitoring & Troubleshooting

### Stream Monitoring

```python
import threading
import time

def monitor_pipeline(pipeline, interval=60):
    """Monitor pipeline in background"""
    while True:
        status = pipeline.get_stream_status()
        print(f"Pipeline Status: {status['pipeline_status']}")
        
        for stream_name, stream_info in status['streams'].items():
            progress = stream_info['progress']
            print(f"Stream: {stream_name}")
            print(f"  Active: {stream_info['active']}")
            print(f"  Input Rate: {progress.get('inputRowsPerSecond', 0):.2f} rows/sec")
            print(f"  Processing Rate: {progress.get('processedRowsPerSecond', 0):.2f} rows/sec")
            print(f"  Total Processed: {progress.get('numProcessedRows', 0)} rows")
        
        time.sleep(interval)

# Start monitoring in background
monitor_thread = threading.Thread(
    target=monitor_pipeline,
    args=(pipeline,),
    daemon=True
)
monitor_thread.start()
```

---

### Error Handling

```python
import logging

logger = logging.getLogger(__name__)

try:
    # Enable fault tolerance first
    pipeline.enable_fault_tolerance(
        checkpoint_dir="/data/checkpoints",
        log_dir="/var/log/spark"
    )
    
    # Read from Kafka
    df = pipeline.read_kafka_stream(schema=schema)
    
    # Validate schema
    is_valid, errors = pipeline.validate_stream_schema(df, expected_columns)
    if not is_valid:
        logger.error(f"Schema validation failed: {errors}")
        raise ValueError(f"Invalid schema: {errors}")
    
    # Add quality checks
    df_quality = pipeline.add_data_quality_checks(df, quality_rules)
    
    # Write to Oracle
    query = pipeline.write_to_oracle(
        df=df_quality,
        table_name="orders_processed",
        checkpoint_location="/data/checkpoints/orders"
    )
    
    query.awaitTermination()
    
except Exception as e:
    logger.error(f"Pipeline error: {str(e)}", exc_info=True)
    pipeline.stop_all_streams()
    raise
```

---

### Common Issues

#### Issue 1: Kafka Connection Timeout

**Symptom**: "Failed to connect to broker"

**Solution**:
```python
# Verify Kafka is running
# kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# Check network connectivity
import socket
socket.create_connection(("localhost", 9092), timeout=5)

# Increase timeout
kafka_config = KafkaConfig(
    bootstrap_servers="localhost:9092",
    topic="orders",
    group_id="consumer",
    session_timeout_ms=60000  # Increased timeout
)
```

---

#### Issue 2: Oracle Connection Error

**Symptom**: "ORA-12514: TNS:listener does not currently know of service"

**Solution**:
```sql
-- Verify Oracle listener is running
-- sqlplus sys/password@XE as sysdba
-- SQL> status

-- Check Oracle configuration
-- Check /etc/sqlnet.ora for correct service names

# Test connection
from sqlalchemy import create_engine
engine = create_engine(oracle_config.get_connection_string())
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1 FROM dual"))
    print(result.fetchone())
```

---

#### Issue 3: Out of Memory Error

**Symptom**: "java.lang.OutOfMemoryError: Java heap space"

**Solution**:
```python
# Increase Spark memory
spark = SparkSession.builder \
    .appName("KafkaOracle") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

# Reduce batch size
query = pipeline.write_to_oracle(
    df=df,
    table_name="orders",
    trigger_interval="60 seconds"  # Larger batches
)
```

---

## Performance Optimization

### 1. Kafka Optimization

```python
kafka_config = KafkaConfig(
    bootstrap_servers="localhost:9092",
    topic="orders",
    group_id="consumer",
    max_poll_records=1000,              # Larger batches
    session_timeout_ms=30000
)

# Kafka broker configuration
# num.network.threads=8
# num.io.threads=8
# compression.type=snappy
```

---

### 2. Spark Streaming Optimization

```python
spark = SparkSession.builder \
    .appName("KafkaOracle") \
    .master("local[*]") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.skewJoin.enabled", "true") \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.default.parallelism", "200") \
    .config("spark.sql.streaming.minBatchesToRetain", "10") \
    .config("spark.sql.streaming.maxBatchesToRetain", "100") \
    .getOrCreate()

# Adjust micro-batch interval
query = pipeline.write_to_oracle(
    df=df,
    table_name="orders",
    trigger_interval="10 seconds"  # Smaller = lower latency, higher overhead
)
```

---

### 3. Oracle Write Optimization

```python
# Batch writes with larger micro-batches
query = pipeline.write_to_oracle(
    df=df,
    table_name="orders",
    mode="append",
    trigger_interval="60 seconds"  # Larger batches
)

# Enable parallel inserts in Oracle
# ALTER SYSTEM SET parallel_max_servers=8;
# ALTER SYSTEM SET parallel_min_servers=4;

# Use bulk insert for initial load
pipeline.write_to_oracle_jdbc(
    df_initial,
    "orders",
    mode="append"
)
```

---

### 4. Checkpointing Optimization

```python
# Use fast storage (SSD) for checkpoints
pipeline.enable_fault_tolerance(
    checkpoint_dir="/mnt/ssd/checkpoints",  # SSD for speed
    log_dir="/var/log/spark"
)

# Compression for checkpoint overhead
spark.conf.set(
    "spark.sql.streaming.checkpointFileManagerType",
    "s3a"  # For cloud storage
)
```

---

## Deployment Guide

### Docker Deployment

```dockerfile
FROM apache/spark:3.5.0

# Install dependencies
RUN pip install pyspark==3.5.0 \
    kafka-python==2.0.2 \
    cx-Oracle==8.3.0 \
    sqlalchemy==2.0.0 \
    pandas==2.0.0

# Copy application
COPY kafka_oracle_streaming.py /app/
COPY kafka_oracle_examples.py /app/

# Run streaming job
CMD ["spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0", \
     "--driver-memory", "4g", \
     "--executor-memory", "4g", \
     "/app/streaming_job.py"]
```

---

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kafka-oracle-streaming
spec:
  containers:
  - name: spark-streaming
    image: kafka-oracle-streaming:latest
    resources:
      requests:
        memory: "4Gi"
        cpu: "2"
      limits:
        memory: "8Gi"
        cpu: "4"
    volumeMounts:
    - name: checkpoint-storage
      mountPath: /data/checkpoints
    env:
    - name: KAFKA_BOOTSTRAP_SERVERS
      value: "kafka-broker:9092"
    - name: ORACLE_HOST
      value: "oracle-db"
  volumes:
  - name: checkpoint-storage
    emptyDir: {}
```

---

### Production Checklist

- ✅ Enable fault tolerance with persistent checkpoint storage
- ✅ Configure monitoring and alerting
- ✅ Set up log aggregation
- ✅ Implement circuit breaker pattern for Oracle writes
- ✅ Configure resource limits (memory, CPU)
- ✅ Test failover and recovery scenarios
- ✅ Document runbooks for common issues
- ✅ Set up dead letter queues for bad messages
- ✅ Implement retry logic with exponential backoff
- ✅ Monitor Kafka consumer lag
- ✅ Configure backups for checkpoint data

---

## Best Practices

### 1. Always Enable Checkpointing

```python
pipeline.enable_fault_tolerance(
    checkpoint_dir="/persistent/checkpoints"
)
```

### 2. Validate Schema Early

```python
is_valid, errors = pipeline.validate_stream_schema(df, expected_columns)
assert is_valid, f"Schema invalid: {errors}"
```

### 3. Handle Duplicates

```python
df_dedup = pipeline.deduplicate_stream(
    df,
    subset=["unique_id"],
    within_window="1 hour"
)
```

### 4. Quality Check Before Writing

```python
df_quality = pipeline.add_data_quality_checks(df, rules)
df_good = df_quality.filter(
    all(col(f"quality_{rule}") for rule in rules.keys())
)
```

### 5. Monitor Continuously

```python
threading.Thread(
    target=pipeline.monitor_streams,
    kwargs={"interval": 60},
    daemon=True
).start()
```

### 6. Implement Graceful Shutdown

```python
try:
    query.awaitTermination()
except KeyboardInterrupt:
    logger.info("Shutting down gracefully...")
    pipeline.stop_all_streams()
```

---

## Conclusion

The Kafka to Oracle Streaming Pipeline provides a production-ready framework for:
- Real-time data ingestion from Kafka
- Complex stream processing with Spark
- Direct persistence to Oracle Database
- Built-in fault tolerance and recovery
- Comprehensive monitoring and validation

For more examples, see `kafka_oracle_examples.py`.
