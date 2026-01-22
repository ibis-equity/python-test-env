"""
Example usage of AWS Spark Routine

This file demonstrates how to use the AWSSparkRoutine class
for common data processing tasks
"""

import json
from aws_spark import (
    AWSSparkRoutine,
    SparkJobOrchestrator,
    spark_operation,
    retry_on_failure
)

# ==================== Example 1: Basic S3 Operations ====================

def example_read_write_s3():
    """Example: Read CSV from S3, transform, write Parquet"""
    
    # Initialize Spark routine
    spark = AWSSparkRoutine(
        app_name="S3-ETL-Job",
        master="spark://localhost:7077"
    )
    
    # Create Spark session
    spark.create_spark_session()
    spark.create_aws_clients()
    
    # Read CSV from S3
    df = spark.read_s3_csv(
        s3_path="s3://my-data-bucket/input/customers.csv",
        header=True,
        infer_schema=True
    )
    
    # Display sample data
    print("Original data:")
    df.show(5)
    
    # Transform: rename columns
    df = spark.rename_columns(
        df,
        mapping={"cust_id": "customer_id", "cust_name": "customer_name"}
    )
    
    # Transform: deduplicate
    df = spark.deduplicate(df, subset=["customer_id"])
    
    # Transform: drop nulls
    df = spark.drop_nulls(df, subset=["customer_id", "customer_name"])
    
    # Write to S3 as Parquet
    spark.write_s3_parquet(
        df,
        s3_path="s3://my-data-bucket/output/customers_processed/",
        mode="overwrite",
        partition_cols=["region"],
        compression="snappy"
    )
    
    spark.stop_session()
    print("ETL job completed successfully!")


# ==================== Example 2: Data Aggregations ====================

def example_aggregations():
    """Example: Group by and aggregations"""
    
    spark = AWSSparkRoutine(app_name="Aggregation-Job")
    spark.create_spark_session()
    spark.create_aws_clients()
    
    # Read sales data
    df = spark.read_s3_parquet("s3://data-bucket/sales_data/")
    
    # Profile the data
    profile = spark.profile_dataframe(df)
    print(f"Row count: {profile['row_count']}")
    print(f"Columns: {profile['columns']}")
    
    # Group by region and product, calculate totals
    aggregated = spark.group_by_aggregate(
        df,
        group_cols=["region", "product"],
        agg_dict={
            "sales_amount": "sum",
            "quantity": "sum",
            "price": "avg"
        }
    )
    
    aggregated.show()
    
    # Write results
    spark.write_s3_csv(
        aggregated,
        s3_path="s3://data-bucket/aggregated_sales/",
        mode="overwrite"
    )
    
    spark.stop_session()


# ==================== Example 3: Window Functions ====================

def example_window_functions():
    """Example: Use window functions for ranking"""
    
    spark = AWSSparkRoutine(app_name="Window-Function-Job")
    spark.create_spark_session()
    spark.create_aws_clients()
    
    # Read data
    df = spark.read_s3_csv("s3://data-bucket/transactions.csv")
    
    # Apply window function - rank transactions by amount within each customer
    df_ranked = spark.window_function(
        df,
        partition_cols=["customer_id"],
        order_cols=["transaction_amount"],
        window_func="row_number"
    )
    
    # Filter to get top 3 transactions per customer
    top_transactions = spark.filter_rows(
        df_ranked,
        "row_num <= 3"
    )
    
    # Write results
    spark.write_s3_parquet(
        top_transactions,
        "s3://data-bucket/top_transactions/"
    )
    
    spark.stop_session()


# ==================== Example 4: Date Operations ====================

def example_date_operations():
    """Example: Extract date components and create date-based columns"""
    
    spark = AWSSparkRoutine(app_name="Date-Processing-Job")
    spark.create_spark_session()
    spark.create_aws_clients()
    
    # Read events data
    df = spark.read_s3_json("s3://data-bucket/events.json")
    
    # Add date columns
    df = spark.add_date_columns(
        df,
        date_column="event_timestamp",
        formats=["year", "month", "day", "quarter"]
    )
    
    # Apply string operations
    df = spark.apply_string_operations(
        df,
        column="event_name",
        operations=["lower", "trim"]
    )
    
    # Write results
    spark.write_s3_parquet(
        df,
        "s3://data-bucket/events_processed/",
        partition_cols=["year", "month"]
    )
    
    spark.stop_session()


# ==================== Example 5: Data Joins ====================

def example_joins():
    """Example: Join multiple DataFrames"""
    
    spark = AWSSparkRoutine(app_name="Join-Job")
    spark.create_spark_session()
    spark.create_aws_clients()
    
    # Read customer and orders data
    customers_df = spark.read_s3_parquet("s3://data-bucket/customers/")
    orders_df = spark.read_s3_parquet("s3://data-bucket/orders/")
    
    # Join on customer_id
    joined_df = spark.join_dataframes(
        left_df=customers_df,
        right_df=orders_df,
        join_keys=["customer_id"],
        join_type="left"
    )
    
    # Select relevant columns
    result_df = spark.select_columns(
        joined_df,
        columns=["customer_id", "customer_name", "order_id", "order_amount", "order_date"]
    )
    
    # Write results
    spark.write_s3_parquet(
        result_df,
        "s3://data-bucket/customer_orders/"
    )
    
    spark.stop_session()


# ==================== Example 6: Data Validation ====================

def example_validation():
    """Example: Validate data schema and quality"""
    
    spark = AWSSparkRoutine(app_name="Validation-Job")
    spark.create_spark_session()
    spark.create_aws_clients()
    
    # Read data
    df = spark.read_s3_csv("s3://data-bucket/products.csv")
    
    # Define expected schema
    expected_schema = {
        "product_id": "string",
        "product_name": "string",
        "price": "double",
        "quantity": "integer",
        "created_date": "timestamp"
    }
    
    # Validate schema
    is_valid, errors = spark.validate_schema(df, expected_schema)
    
    if is_valid:
        print("Schema validation passed!")
    else:
        print("Schema validation failed:")
        for error in errors:
            print(f"  - {error}")
    
    # Fill missing values
    df = spark.fill_nulls(
        df,
        fill_value={"quantity": 0, "price": 0.0}
    )
    
    # Remove remaining nulls
    df = spark.drop_nulls(df)
    
    # Write clean data
    spark.write_s3_parquet(
        df,
        "s3://data-bucket/products_clean/"
    )
    
    spark.stop_session()


# ==================== Example 7: Job Orchestration ====================

def example_orchestration():
    """Example: Orchestrate multiple jobs with dependencies"""
    
    spark = AWSSparkRoutine(app_name="Orchestrated-Jobs")
    spark.create_spark_session()
    spark.create_aws_clients()
    
    orchestrator = SparkJobOrchestrator(spark)
    
    # Define job functions
    def extract_customers():
        print("Extracting customers...")
        df = spark.read_s3_csv("s3://data-bucket/raw/customers.csv")
        return {"rows": df.count()}
    
    def extract_orders():
        print("Extracting orders...")
        df = spark.read_s3_csv("s3://data-bucket/raw/orders.csv")
        return {"rows": df.count()}
    
    def transform_data():
        print("Transforming data...")
        customers = spark.read_s3_csv("s3://data-bucket/customers_extracted/")
        orders = spark.read_s3_csv("s3://data-bucket/orders_extracted/")
        # Perform transformations
        return {"processed": True}
    
    def load_data():
        print("Loading data...")
        # Final loading
        return {"loaded": True}
    
    # Add jobs with dependencies
    orchestrator.add_job("extract_customers", extract_customers)
    orchestrator.add_job("extract_orders", extract_orders)
    orchestrator.add_job("transform_data", transform_data, 
                        dependencies=["extract_customers", "extract_orders"])
    orchestrator.add_job("load_data", load_data, 
                        dependencies=["transform_data"])
    
    # Execute orchestration
    results = orchestrator.execute_jobs()
    
    print("Job Results:")
    for job_name, result in results.items():
        print(f"  {job_name}: {result}")
    
    spark.stop_session()


# ==================== Example 8: With Decorators ====================

@spark_operation
@retry_on_failure(max_retries=3, delay=5)
def example_with_decorators():
    """Example: Using decorators for robust operations"""
    
    spark = AWSSparkRoutine(app_name="Decorator-Job")
    spark.create_spark_session()
    spark.create_aws_clients()
    
    # Read data (with automatic retry on failure)
    df = spark.read_s3_parquet("s3://data-bucket/large_dataset/")
    
    # Cache for multiple operations
    df = spark.cache_dataframe(df)
    
    # Multiple operations on cached data
    df = spark.deduplicate(df)
    df = spark.drop_nulls(df)
    df = spark.apply_string_operations(df, "name", ["trim", "lower"])
    
    # Write results
    spark.write_s3_parquet(df, "s3://data-bucket/output/")
    
    # Cleanup
    spark.uncache_dataframe(df)
    spark.stop_session()
    
    return {"status": "success"}


# ==================== Example 9: Complex ETL Pipeline ====================

def example_complex_pipeline():
    """Example: Complete ETL pipeline with multiple transformations"""
    
    spark = AWSSparkRoutine(app_name="Complex-ETL-Pipeline")
    spark.create_spark_session()
    spark.create_aws_clients()
    
    print("=== Starting Complex ETL Pipeline ===")
    
    # Step 1: Extract data
    print("Step 1: Extracting data...")
    raw_df = spark.read_s3_csv("s3://data-bucket/raw/sales_data.csv")
    print(f"Extracted {raw_df.count()} rows")
    
    # Step 2: Clean data
    print("Step 2: Cleaning data...")
    cleaned_df = spark.drop_nulls(raw_df, subset=["order_id", "customer_id"])
    cleaned_df = spark.deduplicate(cleaned_df, subset=["order_id"])
    print(f"Cleaned to {cleaned_df.count()} rows")
    
    # Step 3: Transform data
    print("Step 3: Transforming data...")
    transformed_df = spark.rename_columns(
        cleaned_df,
        mapping={"order_date": "transaction_date", "order_amt": "amount"}
    )
    transformed_df = spark.add_date_columns(
        transformed_df,
        date_column="transaction_date",
        formats=["year", "month", "day"]
    )
    
    # Step 4: Validate data
    print("Step 4: Validating data...")
    expected_schema = {
        "order_id": "string",
        "customer_id": "string",
        "amount": "double"
    }
    is_valid, errors = spark.validate_schema(transformed_df, expected_schema)
    if is_valid:
        print("Data validation passed!")
    else:
        print("Validation errors found")
    
    # Step 5: Aggregate data
    print("Step 5: Aggregating data...")
    aggregated_df = spark.group_by_aggregate(
        transformed_df,
        group_cols=["year", "month"],
        agg_dict={"amount": "sum"}
    )
    
    # Step 6: Load data
    print("Step 6: Loading data...")
    spark.write_s3_parquet(
        aggregated_df,
        "s3://data-bucket/transformed/monthly_sales/",
        mode="overwrite",
        partition_cols=["year"]
    )
    
    print("=== ETL Pipeline Completed Successfully ===")
    
    spark.stop_session()


if __name__ == "__main__":
    # Run examples
    # example_read_write_s3()
    # example_aggregations()
    # example_window_functions()
    # example_date_operations()
    # example_joins()
    # example_validation()
    # example_orchestration()
    # example_with_decorators()
    example_complex_pipeline()
