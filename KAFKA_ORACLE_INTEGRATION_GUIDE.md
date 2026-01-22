# Kafka to Oracle Integration Guide

## Quick Start

### 1. Installation

```bash
# Install required packages
pip install kafka-python==2.0.2 cx-Oracle==8.3.0 sqlalchemy==2.0.0

# Or use requirements
pip install -r src/requirements.txt
```

### 2. Basic Usage

```python
from pyspark.sql import SparkSession
from aw_spark.kafka_oracle_streaming import (
    KafkaOracleStreamingPipeline,
    KafkaConfig,
    OracleConfig
)

# Initialize Spark
spark = SparkSession.builder \
    .appName("KafkaOracle") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

# Configure
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
    oracle_config=oracle_config
)

# Stream data
df = pipeline.read_kafka_stream()
query = pipeline.write_to_oracle(df, "orders_stream")
query.awaitTermination()
```

---

## Architecture Components

### Component 1: KafkaOracleStreamingPipeline

**Main orchestrator class** that manages:
- Kafka consumer connection
- Spark streaming context
- Oracle database writes
- Checkpointing and recovery
- Monitoring and metrics

**Key Methods**:
- `read_kafka_stream()` - Read from Kafka
- `apply_transformation()` - Transform data
- `apply_windowing()` - Add time windows
- `add_data_quality_checks()` - Validate data
- `write_to_oracle()` - Persist to Oracle
- `monitor_streams()` - Track metrics

### Component 2: KafkaConfig

**Kafka connection parameters**:
```python
kafka_config = KafkaConfig(
    bootstrap_servers="broker1:9092,broker2:9092",
    topic="orders",
    group_id="consumer-group",
    starting_offsets="earliest",
    max_poll_records=500,
    session_timeout_ms=30000
)
```

### Component 3: OracleConfig

**Oracle database parameters**:
```python
oracle_config = OracleConfig(
    host="10.0.1.5",
    port=1521,
    service_name="PROD",
    user="app_user",
    password="secure_password"
)
```

---

## Feature Breakdown

### 1. Stream Reading

**Parse JSON from Kafka**:
```python
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

schema = StructType([
    StructField("order_id", StringType()),
    StructField("amount", DoubleType())
])

df = pipeline.read_kafka_stream(schema=schema)
```

### 2. Data Transformation

**Apply custom transformations**:
```python
from pyspark.sql.functions import col

def enrich_orders(df):
    return df \
        .withColumn("tax", col("amount") * 0.1) \
        .withColumn("total", col("amount") + col("tax"))

df_enriched = pipeline.apply_transformation(df, enrich_orders)
```

### 3. Time Windowing

**Create tumbling/sliding windows**:
```python
# 5-minute tumbling window
df_windowed = pipeline.apply_windowing(
    df, "timestamp", "5 minutes"
)

# 5-minute sliding window (1-minute slide)
df_sliding = pipeline.apply_windowing(
    df, "timestamp", "5 minutes", "1 minute"
)
```

### 4. Aggregations

**Group and aggregate within windows**:
```python
from pyspark.sql.functions import count, sum, avg

df_agg = df_windowed.groupBy("time_window").agg(
    count("order_id").alias("count"),
    sum("amount").alias("total"),
    avg("amount").alias("average")
)
```

### 5. Data Quality

**Add validation columns**:
```python
rules = {
    "valid_amount": lambda df: col("amount") > 0,
    "valid_id": lambda df: col("order_id").isNotNull()
}

df_quality = pipeline.add_data_quality_checks(df, rules)

# Filter good records
df_good = df_quality.filter(
    col("quality_valid_amount") & col("quality_valid_id")
)
```

### 6. Deduplication

**Remove duplicate records**:
```python
df_dedup = pipeline.deduplicate_stream(
    df,
    subset=["transaction_id"],
    within_window="1 hour"
)
```

### 7. Oracle Writes

**Stream to Oracle**:
```python
query = pipeline.write_to_oracle(
    df=df_processed,
    table_name="orders",
    mode="append",
    trigger_interval="30 seconds"
)

# Monitor progress
status = pipeline.get_stream_progress("orders")
print(f"Rate: {status['processedRowsPerSecond']} rows/sec")
```

### 8. Fault Tolerance

**Enable checkpointing**:
```python
pipeline.enable_fault_tolerance(
    checkpoint_dir="/data/checkpoints",
    log_dir="/var/log/spark"
)
```

---

## Streaming Patterns

### Pattern 1: Read-Transform-Write

```python
# 1. Read from Kafka
df = pipeline.read_kafka_stream(schema=order_schema)

# 2. Transform
df = pipeline.apply_transformation(df, transform_func)

# 3. Add metadata
df = pipeline.add_processing_metadata(df)

# 4. Write to Oracle
query = pipeline.write_to_oracle(df, "orders_processed")
```

### Pattern 2: Window-Aggregate-Write

```python
# 1. Apply windowing
df = pipeline.apply_windowing(df, "timestamp", "10 minutes")

# 2. Aggregate
df_agg = df.groupBy("time_window").agg(
    count("id").alias("count"),
    avg("amount").alias("avg_amount")
)

# 3. Write aggregates
query = pipeline.write_to_oracle(df_agg, "metrics_10m")
```

### Pattern 3: Quality-Filter-Split

```python
# 1. Add quality checks
df = pipeline.add_data_quality_checks(df, quality_rules)

# 2. Split good and bad
df_good = df.filter(col("quality_passed") == True)
df_bad = df.filter(col("quality_passed") == False)

# 3. Write separately
q_good = pipeline.write_to_oracle(df_good, "data_valid")
q_bad = pipeline.write_to_oracle(df_bad, "data_invalid")
```

### Pattern 4: Deduplicate-Enrich-Write

```python
# 1. Deduplicate
df = pipeline.deduplicate_stream(df, ["id"], "1 hour")

# 2. Enrich with transformations
df = pipeline.apply_transformation(df, enrich_func)

# 3. Write
query = pipeline.write_to_oracle(df, "orders_deduplicated")
```

---

## Error Handling

### Try-Catch Pattern

```python
try:
    # Enable fault tolerance
    pipeline.enable_fault_tolerance(checkpoint_dir="/data/cp")
    
    # Read and process
    df = pipeline.read_kafka_stream(schema=schema)
    df = pipeline.apply_transformation(df, transform_func)
    
    # Validate
    is_valid, errors = pipeline.validate_stream_schema(df, expected)
    if not is_valid:
        raise ValueError(f"Invalid schema: {errors}")
    
    # Write
    query = pipeline.write_to_oracle(df, "orders")
    query.awaitTermination()
    
except Exception as e:
    logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
    pipeline.stop_all_streams()
    raise
```

### Circuit Breaker Pattern

```python
import time
from functools import wraps

def circuit_breaker(max_failures=5, reset_timeout=60):
    def decorator(func):
        failures = 0
        last_failure_time = None
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal failures, last_failure_time
            
            if failures >= max_failures:
                if time.time() - last_failure_time < reset_timeout:
                    raise Exception("Circuit breaker open")
                failures = 0
            
            try:
                result = func(*args, **kwargs)
                failures = 0
                return result
            except Exception as e:
                failures += 1
                last_failure_time = time.time()
                logger.error(f"Attempt {failures} failed: {str(e)}")
                raise
        
        return wrapper
    return decorator

@circuit_breaker(max_failures=3)
def write_with_circuit_breaker(pipeline, df, table):
    return pipeline.write_to_oracle(df, table)
```

### Retry with Backoff

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, initial_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts")
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}"
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3, initial_delay=2)
def resilient_write(pipeline, df, table):
    return pipeline.write_to_oracle(df, table)
```

---

## Monitoring & Observability

### Real-Time Metrics

```python
import threading
import time
import json

def detailed_monitoring(pipeline, interval=60):
    """Print detailed metrics"""
    while True:
        try:
            status = pipeline.get_stream_status()
            
            print("=" * 60)
            print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Pipeline Status: {status['pipeline_status']}")
            
            for stream_name, stream_data in status['streams'].items():
                print(f"\nStream: {stream_name}")
                print(f"  Active: {stream_data['active']}")
                
                progress = stream_data['progress']
                if progress:
                    print(f"  Input Rate: {progress.get('inputRowsPerSecond', 0):.2f} rows/sec")
                    print(f"  Processing Rate: {progress.get('processedRowsPerSecond', 0):.2f} rows/sec")
                    print(f"  Total Input: {progress.get('numInputRows', 0)} rows")
                    print(f"  Total Processed: {progress.get('numProcessedRows', 0)} rows")
                    print(f"  Batch Duration: {progress.get('batchDuration', 0)}ms")
            
            print("=" * 60)
            time.sleep(interval)
            
        except Exception as e:
            logger.error(f"Monitoring error: {str(e)}")
            time.sleep(interval)

# Start monitoring
monitor_thread = threading.Thread(
    target=detailed_monitoring,
    args=(pipeline, 60),
    daemon=True
)
monitor_thread.start()
```

### Metrics Export (Prometheus)

```python
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Define metrics
records_processed = Counter(
    'kafka_oracle_records_processed_total',
    'Total records processed'
)

processing_rate = Gauge(
    'kafka_oracle_processing_rate',
    'Current processing rate'
)

batch_duration = Histogram(
    'kafka_oracle_batch_duration_seconds',
    'Batch processing duration'
)

def export_metrics(pipeline, port=8000):
    """Export metrics to Prometheus"""
    start_http_server(port)
    
    while True:
        try:
            status = pipeline.get_stream_status()
            
            for stream_data in status['streams'].values():
                progress = stream_data['progress']
                if progress:
                    processing_rate.set(
                        progress.get('processedRowsPerSecond', 0)
                    )
                    batch_duration.observe(
                        progress.get('batchDuration', 0) / 1000
                    )
            
            time.sleep(10)
        except Exception as e:
            logger.error(f"Metrics export error: {str(e)}")
            time.sleep(10)
```

---

## Performance Tuning

### 1. Kafka Tuning

```python
kafka_config = KafkaConfig(
    bootstrap_servers="broker:9092",
    topic="orders",
    group_id="consumer",
    max_poll_records=1000,           # Increase batch size
    session_timeout_ms=30000         # Adjust timeout
)
```

### 2. Spark Tuning

```python
spark = SparkSession.builder \
    .appName("KafkaOracle") \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .getOrCreate()
```

### 3. Write Tuning

```python
# Larger batches = better throughput, higher latency
query = pipeline.write_to_oracle(
    df=df,
    table_name="orders",
    trigger_interval="60 seconds"  # Larger interval
)

# Smaller batches = lower latency, higher overhead
query = pipeline.write_to_oracle(
    df=df,
    table_name="orders",
    trigger_interval="5 seconds"   # Smaller interval
)
```

### 4. Checkpointing Tuning

```python
# Use fast storage (SSD)
pipeline.enable_fault_tolerance(
    checkpoint_dir="/mnt/ssd/checkpoints"
)

# Spark configuration
spark.conf.set(
    "spark.sql.streaming.minBatchesToRetain", "10"
)
spark.conf.set(
    "spark.sql.streaming.maxBatchesToRetain", "100"
)
```

---

## Advanced Features

### Multi-Topic Streaming

```python
# Read from multiple topics
kafka_config.topic = "orders,customers,products"

df = pipeline.read_kafka_stream(schema=order_schema)
```

### Late Data Handling

```python
# Watermark for late data
df_windowed = df.withWatermark("timestamp", "10 minutes") \
    .groupBy(window("timestamp", "5 minutes")) \
    .count()
```

### Stateful Operations

```python
from pyspark.sql.functions import col, sum as spark_sum

# Stateful aggregation across windows
df_stateful = df.groupBy("customer_id") \
    .agg(spark_sum("amount").alias("total_spent"))
```

### Complex Joins

```python
# Join with historical data
df_historical = pipeline.read_oracle_table("customer_history")

df_joined = df.join(
    df_historical,
    on=col("customer_id") == col("hist_customer_id"),
    how="left"
)
```

---

## Troubleshooting

### Issue: "Failed to connect to Kafka"

```python
# Check connectivity
import socket
try:
    socket.create_connection(("localhost", 9092), timeout=5)
    print("Kafka is reachable")
except Exception as e:
    print(f"Cannot reach Kafka: {str(e)}")

# Increase timeout
kafka_config = KafkaConfig(
    bootstrap_servers="localhost:9092",
    topic="orders",
    group_id="consumer",
    session_timeout_ms=60000  # Increased
)
```

### Issue: "Oracle table doesn't exist"

```python
# Create table first
schema_dict = {
    "order_id": "VARCHAR2(50)",
    "amount": "NUMBER(10,2)",
    "created_at": "TIMESTAMP"
}

pipeline.create_oracle_table(
    "orders_stream",
    schema_dict,
    primary_keys=["order_id"]
)
```

### Issue: "Out of memory"

```python
# Increase memory
spark = SparkSession.builder \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.memory", "8g") \
    .config("spark.sql.shuffle.partitions", "100") \
    .getOrCreate()

# Reduce batch size
query = pipeline.write_to_oracle(
    df, "orders",
    trigger_interval="30 seconds"  # Smaller batches
)
```

---

## Production Deployment

### Docker

```dockerfile
FROM apache/spark:3.5.0

RUN pip install kafka-python==2.0.2 \
    cx-Oracle==8.3.0 \
    sqlalchemy==2.0.0

COPY kafka_oracle_streaming.py /app/
COPY entrypoint.py /app/

WORKDIR /app

CMD ["python", "entrypoint.py"]
```

### Kubernetes

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: kafka-oracle-streaming
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: streaming
            image: kafka-oracle:latest
            resources:
              requests:
                memory: "4Gi"
                cpu: "2"
          restartPolicy: Never
```

---

## References

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Apache Spark Streaming Guide](https://spark.apache.org/docs/latest/streaming-programming-guide.html)
- [Oracle Database Documentation](https://docs.oracle.com/en/database/)
- [PySpark API](https://spark.apache.org/docs/latest/api/python/)
