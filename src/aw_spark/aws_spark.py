"""
AWS Spark Routine for Data Processing

This module provides comprehensive functionality for:
- Spark session management with AWS integration
- Data reading/writing from S3, RDS, Redshift
- Data transformations and aggregations
- Partitioning and optimization
- Job orchestration and monitoring
"""

import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from functools import wraps
from pyspark.sql import SparkSession, DataFrame, Window
from pyspark.sql.functions import (
    col, when, concat_ws, row_number, dense_rank, 
    sum as spark_sum, count, avg, min, max,
    lower, upper, trim, length,
    year, month, day, date_format, to_date,
    explode, arrays_zip, flatten
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class SparkJobException(Exception):
    """Custom exception for Spark job errors"""
    pass


class AWSSparkRoutine:
    """
    Main class for AWS Spark operations
    Handles session creation, data I/O, and transformations
    """

    def __init__(
        self,
        app_name: str = "AWS-Spark-Job",
        master: str = "spark://localhost:7077",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: str = "us-east-1"
    ):
        """
        Initialize AWS Spark routine
        
        Args:
            app_name: Spark application name
            master: Spark master URL
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
            aws_region: AWS region
        """
        self.app_name = app_name
        self.master = master
        self.aws_region = aws_region
        self.session = None
        self.s3_client = None
        self.rds_client = None
        self.redshift_client = None
        
        # Setup AWS credentials
        if aws_access_key_id and aws_secret_access_key:
            os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
            os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
        
        self.aws_access_key_id = aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        
        logger.info(f"Initializing AWS Spark Routine: {app_name}")

    def create_spark_session(self) -> SparkSession:
        """
        Create and configure Spark session with AWS support
        
        Returns:
            SparkSession: Configured Spark session
        """
        try:
            self.session = SparkSession.builder \
                .master(self.master) \
                .appName(self.app_name) \
                .config("spark.hadoop.fs.s3a.access.key", self.aws_access_key_id or "") \
                .config("spark.hadoop.fs.s3a.secret.key", self.aws_secret_access_key or "") \
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.2.1") \
                .config("spark.sql.shuffle.partitions", "200") \
                .config("spark.executor.memory", "4g") \
                .config("spark.driver.memory", "2g") \
                .getOrCreate()
            
            logger.info("Spark session created successfully")
            return self.session
        except Exception as e:
            logger.error(f"Error creating Spark session: {str(e)}")
            raise SparkJobException(f"Failed to create Spark session: {str(e)}")

    def create_aws_clients(self) -> None:
        """Create AWS service clients"""
        try:
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
            self.rds_client = boto3.client('rds', region_name=self.aws_region)
            self.redshift_client = boto3.client('redshift', region_name=self.aws_region)
            logger.info("AWS clients created successfully")
        except ClientError as e:
            logger.error(f"Error creating AWS clients: {str(e)}")
            raise SparkJobException(f"Failed to create AWS clients: {str(e)}")

    # ==================== S3 Operations ====================

    def read_s3_csv(
        self,
        s3_path: str,
        header: bool = True,
        infer_schema: bool = True,
        delimiter: str = ","
    ) -> DataFrame:
        """
        Read CSV file from S3
        
        Args:
            s3_path: S3 path (s3://bucket/path)
            header: First row is header
            infer_schema: Infer schema from data
            delimiter: Column delimiter
            
        Returns:
            DataFrame: Spark DataFrame
        """
        try:
            logger.info(f"Reading CSV from S3: {s3_path}")
            df = self.session.read \
                .option("header", header) \
                .option("inferSchema", infer_schema) \
                .option("delimiter", delimiter) \
                .csv(s3_path)
            
            logger.info(f"Successfully read CSV: {df.count()} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error reading CSV from S3: {str(e)}")
            raise SparkJobException(f"Failed to read CSV from S3: {str(e)}")

    def read_s3_parquet(self, s3_path: str) -> DataFrame:
        """
        Read Parquet file from S3
        
        Args:
            s3_path: S3 path (s3://bucket/path)
            
        Returns:
            DataFrame: Spark DataFrame
        """
        try:
            logger.info(f"Reading Parquet from S3: {s3_path}")
            df = self.session.read.parquet(s3_path)
            logger.info(f"Successfully read Parquet: {df.count()} rows")
            return df
        except Exception as e:
            logger.error(f"Error reading Parquet from S3: {str(e)}")
            raise SparkJobException(f"Failed to read Parquet from S3: {str(e)}")

    def read_s3_json(self, s3_path: str, multiline: bool = False) -> DataFrame:
        """
        Read JSON file from S3
        
        Args:
            s3_path: S3 path (s3://bucket/path)
            multiline: Support multiline JSON
            
        Returns:
            DataFrame: Spark DataFrame
        """
        try:
            logger.info(f"Reading JSON from S3: {s3_path}")
            df = self.session.read \
                .option("multiLine", multiline) \
                .json(s3_path)
            logger.info(f"Successfully read JSON: {df.count()} rows")
            return df
        except Exception as e:
            logger.error(f"Error reading JSON from S3: {str(e)}")
            raise SparkJobException(f"Failed to read JSON from S3: {str(e)}")

    def write_s3_csv(
        self,
        df: DataFrame,
        s3_path: str,
        mode: str = "overwrite",
        header: bool = True,
        partition_cols: Optional[List[str]] = None
    ) -> None:
        """
        Write DataFrame to S3 as CSV
        
        Args:
            df: Spark DataFrame
            s3_path: S3 output path
            mode: Write mode (overwrite, append, ignore, error)
            header: Write header row
            partition_cols: Columns to partition by
        """
        try:
            logger.info(f"Writing CSV to S3: {s3_path}")
            write_df = df.coalesce(1) if not partition_cols else df
            
            write_df.write \
                .mode(mode) \
                .option("header", header) \
                .csv(s3_path)
            
            logger.info(f"Successfully wrote CSV to S3")
        except Exception as e:
            logger.error(f"Error writing CSV to S3: {str(e)}")
            raise SparkJobException(f"Failed to write CSV to S3: {str(e)}")

    def write_s3_parquet(
        self,
        df: DataFrame,
        s3_path: str,
        mode: str = "overwrite",
        partition_cols: Optional[List[str]] = None,
        compression: str = "snappy"
    ) -> None:
        """
        Write DataFrame to S3 as Parquet
        
        Args:
            df: Spark DataFrame
            s3_path: S3 output path
            mode: Write mode
            partition_cols: Columns to partition by
            compression: Compression codec (snappy, gzip, etc)
        """
        try:
            logger.info(f"Writing Parquet to S3: {s3_path}")
            
            if partition_cols:
                df.write \
                    .mode(mode) \
                    .option("compression", compression) \
                    .partitionBy(partition_cols) \
                    .parquet(s3_path)
            else:
                df.coalesce(1).write \
                    .mode(mode) \
                    .option("compression", compression) \
                    .parquet(s3_path)
            
            logger.info(f"Successfully wrote Parquet to S3")
        except Exception as e:
            logger.error(f"Error writing Parquet to S3: {str(e)}")
            raise SparkJobException(f"Failed to write Parquet to S3: {str(e)}")

    def write_s3_json(
        self,
        df: DataFrame,
        s3_path: str,
        mode: str = "overwrite"
    ) -> None:
        """
        Write DataFrame to S3 as JSON
        
        Args:
            df: Spark DataFrame
            s3_path: S3 output path
            mode: Write mode
        """
        try:
            logger.info(f"Writing JSON to S3: {s3_path}")
            df.coalesce(1).write.mode(mode).json(s3_path)
            logger.info(f"Successfully wrote JSON to S3")
        except Exception as e:
            logger.error(f"Error writing JSON to S3: {str(e)}")
            raise SparkJobException(f"Failed to write JSON to S3: {str(e)}")

    # ==================== Data Transformations ====================

    def deduplicate(
        self,
        df: DataFrame,
        subset: Optional[List[str]] = None
    ) -> DataFrame:
        """
        Remove duplicate rows
        
        Args:
            df: Input DataFrame
            subset: Columns to consider for duplicates (None = all columns)
            
        Returns:
            DataFrame: Deduplicated DataFrame
        """
        try:
            logger.info(f"Deduplicating DataFrame")
            if subset:
                result_df = df.dropDuplicates(subset)
            else:
                result_df = df.dropDuplicates()
            
            logger.info(f"Deduplication complete: {result_df.count()} rows remaining")
            return result_df
        except Exception as e:
            logger.error(f"Error deduplicating DataFrame: {str(e)}")
            raise SparkJobException(f"Failed to deduplicate DataFrame: {str(e)}")

    def fill_nulls(
        self,
        df: DataFrame,
        fill_value: Dict[str, Any]
    ) -> DataFrame:
        """
        Fill null values in DataFrame
        
        Args:
            df: Input DataFrame
            fill_value: Dict mapping column names to fill values
            
        Returns:
            DataFrame: DataFrame with nulls filled
        """
        try:
            logger.info(f"Filling null values with {fill_value}")
            result_df = df.fillna(fill_value)
            logger.info(f"Null values filled")
            return result_df
        except Exception as e:
            logger.error(f"Error filling null values: {str(e)}")
            raise SparkJobException(f"Failed to fill null values: {str(e)}")

    def drop_nulls(
        self,
        df: DataFrame,
        subset: Optional[List[str]] = None,
        how: str = "any"
    ) -> DataFrame:
        """
        Remove rows with null values
        
        Args:
            df: Input DataFrame
            subset: Columns to check for nulls (None = all)
            how: "any" or "all" - drop if any or all nulls
            
        Returns:
            DataFrame: DataFrame with nulls dropped
        """
        try:
            logger.info(f"Dropping rows with null values (how={how})")
            result_df = df.dropna(subset=subset, how=how)
            logger.info(f"Dropped null rows: {result_df.count()} rows remaining")
            return result_df
        except Exception as e:
            logger.error(f"Error dropping null values: {str(e)}")
            raise SparkJobException(f"Failed to drop null values: {str(e)}")

    def rename_columns(
        self,
        df: DataFrame,
        mapping: Dict[str, str]
    ) -> DataFrame:
        """
        Rename columns in DataFrame
        
        Args:
            df: Input DataFrame
            mapping: Dict mapping old names to new names
            
        Returns:
            DataFrame: DataFrame with renamed columns
        """
        try:
            logger.info(f"Renaming columns: {mapping}")
            result_df = df
            for old_name, new_name in mapping.items():
                result_df = result_df.withColumnRenamed(old_name, new_name)
            
            logger.info(f"Columns renamed successfully")
            return result_df
        except Exception as e:
            logger.error(f"Error renaming columns: {str(e)}")
            raise SparkJobException(f"Failed to rename columns: {str(e)}")

    def select_columns(
        self,
        df: DataFrame,
        columns: List[str]
    ) -> DataFrame:
        """
        Select specific columns from DataFrame
        
        Args:
            df: Input DataFrame
            columns: List of column names to select
            
        Returns:
            DataFrame: DataFrame with selected columns
        """
        try:
            logger.info(f"Selecting columns: {columns}")
            result_df = df.select(columns)
            logger.info(f"Selected {len(columns)} columns")
            return result_df
        except Exception as e:
            logger.error(f"Error selecting columns: {str(e)}")
            raise SparkJobException(f"Failed to select columns: {str(e)}")

    def filter_rows(
        self,
        df: DataFrame,
        condition: str
    ) -> DataFrame:
        """
        Filter rows based on condition
        
        Args:
            df: Input DataFrame
            condition: SQL filter condition
            
        Returns:
            DataFrame: Filtered DataFrame
        """
        try:
            logger.info(f"Filtering rows with condition: {condition}")
            result_df = df.filter(condition)
            logger.info(f"Filtering complete: {result_df.count()} rows remaining")
            return result_df
        except Exception as e:
            logger.error(f"Error filtering rows: {str(e)}")
            raise SparkJobException(f"Failed to filter rows: {str(e)}")

    # ==================== Aggregations ====================

    def group_by_aggregate(
        self,
        df: DataFrame,
        group_cols: List[str],
        agg_dict: Dict[str, str]
    ) -> DataFrame:
        """
        Group by columns and aggregate
        
        Args:
            df: Input DataFrame
            group_cols: Columns to group by
            agg_dict: Dict mapping column names to aggregation functions
                     (e.g., {"sales": "sum", "price": "avg"})
            
        Returns:
            DataFrame: Aggregated DataFrame
        """
        try:
            logger.info(f"Grouping by {group_cols} with aggregations {agg_dict}")
            
            # Build aggregation expressions
            agg_exprs = {}
            for col_name, agg_func in agg_dict.items():
                if agg_func.lower() == "sum":
                    agg_exprs[col_name] = "sum"
                elif agg_func.lower() == "avg":
                    agg_exprs[col_name] = "avg"
                elif agg_func.lower() == "count":
                    agg_exprs[col_name] = "count"
                elif agg_func.lower() == "min":
                    agg_exprs[col_name] = "min"
                elif agg_func.lower() == "max":
                    agg_exprs[col_name] = "max"
            
            result_df = df.groupBy(group_cols).agg(agg_exprs)
            logger.info(f"Aggregation complete: {result_df.count()} groups")
            return result_df
        except Exception as e:
            logger.error(f"Error in group by aggregation: {str(e)}")
            raise SparkJobException(f"Failed to perform group by aggregation: {str(e)}")

    def window_function(
        self,
        df: DataFrame,
        partition_cols: List[str],
        order_cols: List[str],
        window_func: str = "row_number"
    ) -> DataFrame:
        """
        Apply window functions
        
        Args:
            df: Input DataFrame
            partition_cols: Columns to partition by
            order_cols: Columns to order by
            window_func: Window function (row_number, rank, dense_rank)
            
        Returns:
            DataFrame: DataFrame with window function applied
        """
        try:
            logger.info(f"Applying window function: {window_func}")
            
            window = Window.partitionBy(partition_cols).orderBy(order_cols)
            
            if window_func == "row_number":
                result_df = df.withColumn("row_num", row_number().over(window))
            elif window_func == "rank":
                result_df = df.withColumn("rank", dense_rank().over(window))
            else:
                raise ValueError(f"Unknown window function: {window_func}")
            
            logger.info(f"Window function applied successfully")
            return result_df
        except Exception as e:
            logger.error(f"Error applying window function: {str(e)}")
            raise SparkJobException(f"Failed to apply window function: {str(e)}")

    # ==================== String Operations ====================

    def apply_string_operations(
        self,
        df: DataFrame,
        column: str,
        operations: List[str]
    ) -> DataFrame:
        """
        Apply string operations to column
        
        Args:
            df: Input DataFrame
            column: Column to operate on
            operations: List of operations (lower, upper, trim, length)
            
        Returns:
            DataFrame: DataFrame with operations applied
        """
        try:
            logger.info(f"Applying string operations: {operations}")
            result_df = df
            
            for op in operations:
                if op.lower() == "lower":
                    result_df = result_df.withColumn(column, lower(col(column)))
                elif op.lower() == "upper":
                    result_df = result_df.withColumn(column, upper(col(column)))
                elif op.lower() == "trim":
                    result_df = result_df.withColumn(column, trim(col(column)))
                elif op.lower() == "length":
                    result_df = result_df.withColumn(f"{column}_length", length(col(column)))
            
            logger.info(f"String operations applied successfully")
            return result_df
        except Exception as e:
            logger.error(f"Error applying string operations: {str(e)}")
            raise SparkJobException(f"Failed to apply string operations: {str(e)}")

    # ==================== Date Operations ====================

    def add_date_columns(
        self,
        df: DataFrame,
        date_column: str,
        formats: List[str] = None
    ) -> DataFrame:
        """
        Add date-based columns from date column
        
        Args:
            df: Input DataFrame
            date_column: Column with date values
            formats: Formats to extract (year, month, day, quarter, date_format)
            
        Returns:
            DataFrame: DataFrame with date columns added
        """
        try:
            if not formats:
                formats = ["year", "month", "day"]
            
            logger.info(f"Adding date columns: {formats}")
            result_df = df
            
            for fmt in formats:
                if fmt.lower() == "year":
                    result_df = result_df.withColumn("year", year(col(date_column)))
                elif fmt.lower() == "month":
                    result_df = result_df.withColumn("month", month(col(date_column)))
                elif fmt.lower() == "day":
                    result_df = result_df.withColumn("day", day(col(date_column)))
                elif fmt.lower() == "quarter":
                    result_df = result_df.withColumn(
                        "quarter",
                        ((month(col(date_column)) - 1) / 3).cast("int") + 1
                    )
            
            logger.info(f"Date columns added successfully")
            return result_df
        except Exception as e:
            logger.error(f"Error adding date columns: {str(e)}")
            raise SparkJobException(f"Failed to add date columns: {str(e)}")

    # ==================== Data Profiling ====================

    def profile_dataframe(self, df: DataFrame) -> Dict[str, Any]:
        """
        Generate profile statistics for DataFrame
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dict: Profile statistics
        """
        try:
            logger.info("Profiling DataFrame")
            profile = {
                "row_count": df.count(),
                "column_count": len(df.columns),
                "columns": df.columns,
                "schema": df.schema.jsonValue(),
                "dtypes": {field.name: field.dataType.typeName() for field in df.schema.fields},
                "memory_usage": df.rdd.map(lambda x: sys.getsizeof(x)).sum() if 'sys' in dir() else None
            }
            
            # Calculate null percentages
            null_counts = {}
            for col_name in df.columns:
                null_count = df.filter(col(col_name).isNull()).count()
                null_counts[col_name] = (null_count / profile["row_count"]) * 100
            
            profile["null_percentages"] = null_counts
            logger.info(f"Profile generated: {profile['row_count']} rows")
            return profile
        except Exception as e:
            logger.error(f"Error profiling DataFrame: {str(e)}")
            raise SparkJobException(f"Failed to profile DataFrame: {str(e)}")

    # ==================== Data Validation ====================

    def validate_schema(
        self,
        df: DataFrame,
        expected_schema: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate DataFrame schema against expected schema
        
        Args:
            df: Input DataFrame
            expected_schema: Dict mapping column names to expected types
            
        Returns:
            Tuple: (is_valid, list_of_errors)
        """
        try:
            logger.info("Validating schema")
            errors = []
            
            actual_schema = {field.name: field.dataType.typeName() for field in df.schema.fields}
            
            # Check expected columns exist
            for col_name, expected_type in expected_schema.items():
                if col_name not in actual_schema:
                    errors.append(f"Missing column: {col_name}")
                elif actual_schema[col_name] != expected_type:
                    errors.append(f"Column {col_name}: expected {expected_type}, got {actual_schema[col_name]}")
            
            is_valid = len(errors) == 0
            logger.info(f"Schema validation: {'PASSED' if is_valid else 'FAILED'}")
            return is_valid, errors
        except Exception as e:
            logger.error(f"Error validating schema: {str(e)}")
            raise SparkJobException(f"Failed to validate schema: {str(e)}")

    # ==================== Join Operations ====================

    def join_dataframes(
        self,
        left_df: DataFrame,
        right_df: DataFrame,
        join_keys: List[str],
        join_type: str = "inner"
    ) -> DataFrame:
        """
        Join two DataFrames
        
        Args:
            left_df: Left DataFrame
            right_df: Right DataFrame
            join_keys: Column names to join on
            join_type: Join type (inner, left, right, outer)
            
        Returns:
            DataFrame: Joined DataFrame
        """
        try:
            logger.info(f"Joining DataFrames on {join_keys} with {join_type} join")
            
            # Build join condition
            join_condition = None
            for key in join_keys:
                if join_condition is None:
                    join_condition = left_df[key] == right_df[key]
                else:
                    join_condition = join_condition & (left_df[key] == right_df[key])
            
            result_df = left_df.join(right_df, join_condition, join_type)
            logger.info(f"Join complete: {result_df.count()} rows")
            return result_df
        except Exception as e:
            logger.error(f"Error joining DataFrames: {str(e)}")
            raise SparkJobException(f"Failed to join DataFrames: {str(e)}")

    # ==================== Cleanup ====================

    def stop_session(self) -> None:
        """Stop Spark session"""
        try:
            if self.session:
                self.session.stop()
                logger.info("Spark session stopped")
        except Exception as e:
            logger.error(f"Error stopping Spark session: {str(e)}")

    def cache_dataframe(self, df: DataFrame) -> DataFrame:
        """
        Cache DataFrame in memory
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame: Cached DataFrame
        """
        try:
            df.cache()
            df.count()  # Trigger caching
            logger.info("DataFrame cached successfully")
            return df
        except Exception as e:
            logger.error(f"Error caching DataFrame: {str(e)}")
            raise SparkJobException(f"Failed to cache DataFrame: {str(e)}")

    def uncache_dataframe(self, df: DataFrame) -> None:
        """
        Remove DataFrame from cache
        
        Args:
            df: Input DataFrame
        """
        try:
            df.unpersist()
            logger.info("DataFrame uncached successfully")
        except Exception as e:
            logger.error(f"Error uncaching DataFrame: {str(e)}")


class SparkJobOrchestrator:
    """
    Orchestrate multiple Spark jobs
    """

    def __init__(self, spark_routine: AWSSparkRoutine):
        """
        Initialize orchestrator
        
        Args:
            spark_routine: AWSSparkRoutine instance
        """
        self.spark_routine = spark_routine
        self.jobs = []
        self.job_results = {}

    def add_job(
        self,
        job_name: str,
        job_func,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Add job to orchestration
        
        Args:
            job_name: Name of the job
            job_func: Function to execute
            dependencies: List of job names this depends on
        """
        self.jobs.append({
            "name": job_name,
            "func": job_func,
            "dependencies": dependencies or []
        })
        logger.info(f"Added job: {job_name}")

    def execute_jobs(self) -> Dict[str, Any]:
        """
        Execute all jobs in dependency order
        
        Returns:
            Dict: Job results mapping
        """
        logger.info(f"Starting job execution: {len(self.jobs)} jobs")
        
        # Topological sort for dependencies
        executed = set()
        
        while len(executed) < len(self.jobs):
            executed_this_round = False
            
            for job in self.jobs:
                if job["name"] in executed:
                    continue
                
                # Check if dependencies are satisfied
                if all(dep in executed for dep in job["dependencies"]):
                    try:
                        logger.info(f"Executing job: {job['name']}")
                        result = job["func"]()
                        self.job_results[job["name"]] = result
                        executed.add(job["name"])
                        executed_this_round = True
                        logger.info(f"Job completed: {job['name']}")
                    except Exception as e:
                        logger.error(f"Job failed: {job['name']}: {str(e)}")
                        self.job_results[job["name"]] = {"error": str(e)}
            
            if not executed_this_round and len(executed) < len(self.jobs):
                logger.error("Circular dependency detected")
                raise SparkJobException("Circular dependency in jobs")
        
        logger.info(f"All jobs completed")
        return self.job_results


# ==================== Decorators ====================

def spark_operation(func):
    """Decorator for Spark operations with error handling and logging"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        operation_name = func.__name__
        logger.info(f"Starting operation: {operation_name}")
        
        try:
            start_time = datetime.now()
            result = func(*args, **kwargs)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Operation completed: {operation_name} ({elapsed:.2f}s)")
            return result
        except Exception as e:
            logger.error(f"Operation failed: {operation_name}: {str(e)}")
            raise SparkJobException(f"Operation {operation_name} failed: {str(e)}")
    
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: int = 5):
    """Decorator to retry failed operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
                        raise
        return wrapper
    return decorator
