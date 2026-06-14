# Kafka to Oracle Streaming - Quick Reference

## Installation

```bash
pip install kafka-python cx-Oracle sqlalchemy pyspark
```

## Basic Setup

```python
from pyspark.sql import SparkSession
from aw_spark.kafka_oracle_streaming import (
    KafkaOracleStreamingPipeline,
    KafkaConfig,
    OracleConfig
)

# Create Spark session
spark = SparkSession.builder \
    .appName("KafkaOracle") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

# Configure
kafka_config = KafkaConfig(
    bootstrap_servers="localhost:9092",
    topic="orders",
    group_id="consumer"
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
```

---

## Common Operations

### Read from Kafka

```python
# Without schema (raw data)
df = pipeline.read_kafka_stream()

# With schema (typed)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
schema = StructType([
    StructField("order_id", StringType()),
    StructField("amount", DoubleType())
])
df = pipeline.read_kafka_stream(schema=schema)
```

### Transform Data

```python
from pyspark.sql.functions import col

# Custom transformation
def my_transform(df):
    return df.withColumn("amount_usd", col("amount") * 1.1)

df = pipeline.apply_transformation(df, my_transform)
```

### Add Metadata

```python
df = pipeline.add_processing_metadata(df)
# Adds: processed_at, pipeline_name, processing_date
```

### Apply Window

```python
# Tumbling window (5 minutes)
df = pipeline.apply_windowing(df, "timestamp", "5 minutes")

# Sliding window (5 minutes, 1 minute slide)
df = pipeline.apply_windowing(df, "timestamp", "5 minutes", "1 minute")
```

### Filter Stream

```python
df = pipeline.filter_stream(df, "amount > 1000")
```

### Deduplicate

```python
# Remove duplicates within 1 hour
df = pipeline.deduplicate_stream(df, ["transaction_id"], "1 hour")
```

### Quality Checks

```python
rules = {
    "valid_amount": lambda df: (col("amount") > 0) & (col("amount") < 100000),
    "valid_id": lambda df: col("order_id").isNotNull()
}

df = pipeline.add_data_quality_checks(df, rules)

# Filter good records
df_good = df.filter(col("quality_valid_amount") & col("quality_valid_id"))
```

### Write to Oracle

```python
# Stream write
query = pipeline.write_to_oracle(
    df=df,
    table_name="orders",
    mode="append",
    trigger_interval="30 seconds"
)

# Wait for termination
query.awaitTermination()
```

### Validate Schema

```python
expected = {
    "order_id": "string",
    "amount": "double"
}
is_valid, errors = pipeline.validate_stream_schema(df, expected)
if not is_valid:
    print(f"Schema errors: {errors}")
```

### Get Progress

```python
progress = pipeline.get_stream_progress("stream_name")
print(f"Rate: {progress['processedRowsPerSecond']} rows/sec")
print(f"Total: {progress['numProcessedRows']} rows")
```

### Monitor Streams

```python
import threading
monitor = threading.Thread(
    target=pipeline.monitor_streams,
    kwargs={"interval": 60},
    daemon=True
)
monitor.start()
```

### Stop Streams

```python
# Stop single stream
pipeline.stop_stream("stream_name")

# Stop all streams
pipeline.stop_all_streams()
```

### Enable Fault Tolerance

```python
pipeline.enable_fault_tolerance(
    checkpoint_dir="/data/checkpoints",
    log_dir="/var/log/spark"
)
```

### Read Oracle Table

```python
df = pipeline.read_oracle_table("orders_history")
```

### Create Oracle Table

```python
schema = {
    "order_id": "VARCHAR2(50)",
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

## Complete Example

```python
# 1. Initialize
pipeline = KafkaOracleStreamingPipeline(spark, kafka_config, oracle_config)

# 2. Read
df = pipeline.read_kafka_stream(schema=my_schema)

# 3. Transform
df = pipeline.apply_transformation(df, transform_func)

# 4. Add metadata
df = pipeline.add_processing_metadata(df)

# 5. Quality check
df = pipeline.add_data_quality_checks(df, quality_rules)

# 6. Filter
df_good = df.filter(col("quality_passed"))

# 7. Write
query = pipeline.write_to_oracle(df_good, "orders")

# 8. Monitor
try:
    query.awaitTermination()
except KeyboardInterrupt:
    pipeline.stop_all_streams()
```

---

## Aggregations

```python
from pyspark.sql.functions import count, sum as spark_sum, avg

# Window first
df = pipeline.apply_windowing(df, "timestamp", "1 hour")

# Then aggregate
df_agg = df.groupBy("time_window").agg(
    count("id").alias("count"),
    spark_sum("amount").alias("total"),
    avg("amount").alias("average")
)

# Write aggregates
query = pipeline.write_to_oracle(df_agg, "metrics_hourly")
```

---

## Error Handling

```python
import logging

logger = logging.getLogger(__name__)

try:
    # Enable checkpointing
    pipeline.enable_fault_tolerance("/data/checkpoints")
    
    # Process
    df = pipeline.read_kafka_stream(schema=schema)
    
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

---

## Performance Tuning

### Increase Throughput

```python
# Larger batches
query = pipeline.write_to_oracle(
    df, "orders",
    trigger_interval="60 seconds"  # Larger interval
)

# More partitions
spark.conf.set("spark.sql.shuffle.partitions", "300")

# Larger Kafka batches
kafka_config.max_poll_records = 1000
```

### Reduce Latency

```python
# Smaller batches
query = pipeline.write_to_oracle(
    df, "orders",
    trigger_interval="5 seconds"   # Smaller interval
)

# Smaller Kafka batches
kafka_config.max_poll_records = 100
```

### Memory Optimization

```python
# Increase driver/executor memory
spark = SparkSession.builder \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.memory", "8g") \
    .getOrCreate()

# Reduce memory usage
spark.conf.set("spark.sql.shuffle.partitions", "100")
```

---

## Configuration Reference

### KafkaConfig

```python
KafkaConfig(
    bootstrap_servers="broker1:9092,broker2:9092",  # Kafka brokers
    topic="orders",                                  # Topic name
    group_id="consumer-group",                      # Consumer group
    starting_offsets="earliest",                    # Start from earliest
    max_poll_records=500,                           # Records per batch
    session_timeout_ms=30000                        # Session timeout
)
```

### OracleConfig

```python
OracleConfig(
    host="oracle-host",           # Oracle hostname
    port=1521,                     # Oracle port
    service_name="PROD",           # Oracle service name
    user="app_user",               # Database user
    password="password"            # Database password
)
```

---

## Window Durations

```
"1 second"
"5 seconds"
"1 minute"
"5 minutes"
"10 minutes"
"1 hour"
"1 day"
"1 week"
```

---

## Write Modes

| Mode | Behavior |
|------|----------|
| `"append"` | Add new rows |
| `"complete"` | Write entire result set |
| `"update"` | Update changed rows |

---

## Status Values

```
"created"    # Pipeline initialized
"running"    # Actively processing
"stopped"    # Manually stopped
"failed"     # Encountered error
"completed"  # All streams finished
```

---

## Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Show DataFrame schema
df.printSchema()

# Show sample data
df.show()

# Get query status
for query in spark.streams.active:
    print(f"Query: {query.name}")
    print(f"Active: {query.isActive}")
    if query.lastProgress:
        print(f"Rows: {query.lastProgress['numInputRows']}")
```

---

## Common Patterns

### Pattern: Extract → Clean → Load

```python
# Extract
df = pipeline.read_kafka_stream()

# Clean
df = df.dropna(subset=["id"])
df = df.filter(col("amount") > 0)

# Load
query = pipeline.write_to_oracle(df, "clean_data")
```

### Pattern: Validate → Split → Write

```python
# Validate
df = pipeline.add_data_quality_checks(df, rules)

# Split
df_valid = df.filter(col("quality_passed"))
df_invalid = df.filter(~col("quality_passed"))

# Write
q1 = pipeline.write_to_oracle(df_valid, "valid_data")
q2 = pipeline.write_to_oracle(df_invalid, "invalid_data")
```

### Pattern: Window → Aggregate → Write

```python
# Window
df = pipeline.apply_windowing(df, "ts", "1 hour")

# Aggregate
df_agg = df.groupBy("window").agg(count("*"))

# Write
query = pipeline.write_to_oracle(df_agg, "hourly_metrics")
```

---

## Links

- **Full Documentation**: `KAFKA_ORACLE_STREAMING_DOCUMENTATION.md`
- **Integration Guide**: `KAFKA_ORACLE_INTEGRATION_GUIDE.md`
- **Examples**: `src/aw_spark/kafka_oracle_examples.py`
- **Production Code**: `src/aw_spark/kafka_oracle_production.py`

---

## Tips & Tricks

1. **Always enable checkpointing** for production
2. **Validate schema early** to catch errors
3. **Use quality checks** before writing to database
4. **Monitor metrics** continuously
5. **Handle exceptions** gracefully with try-catch
6. **Use deduplication** for high-volume streams
7. **Tune batch interval** for throughput vs latency
8. **Test failover** scenarios before production
9. **Keep checkpoint storage** on fast SSD storage
10. **Document custom transformations** clearly

---

## Support & Resources

- Issues? Check troubleshooting section in main documentation
- Performance? See performance tuning section
- Deployment? Check deployment guide
- Examples? Review kafka_oracle_examples.py
