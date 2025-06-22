#!/usr/bin/env python3
"""
Preprocessing script to create optimized station data from S3 dataset.

This script reads the full CitiBike dataset from S3, extracts unique stations
with averaged coordinates, and saves the result as a local Parquet file.
This version uses a temporary file-based database and a streaming COPY
command to handle larger-than-memory datasets without crashing.

Usage:
    python preprocess_data.py
"""

import duckdb
import os
from datetime import datetime
import time

def create_unique_stations_dataset():
    """
    Create a dataset of unique stations with averaged coordinates from S3 data.
    """
    print(f"[{datetime.now()}] Starting preprocessing of station data...")
    
    # S3 path to the full dataset
    s3_parquet_path = "s3://us-west-2.opendata.source.coop/zluo43/citibike/new_schema_combined_with_geom.parquet/**/*.parquet"
    
    # Create data directory if it doesn't exist
    data_dir = "app/data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Output file path
    output_file = os.path.join(data_dir, "all_stations.parquet")
    
    # Persistent DuckDB file path
    db_file = os.path.join(data_dir, "pre_data_all.db")
    
    # Remove existing database file if it exists (for fresh start)
    if os.path.exists(db_file):
        print(f"[{datetime.now()}] Removing existing database file: {db_file}")
        os.remove(db_file)
    
    # Initialize DuckDB connection with persistent file
    print(f"[{datetime.now()}] Connecting to persistent DuckDB file: {db_file}")
    con = duckdb.connect(database=db_file, read_only=False)
    
    try:
        # Install and load spatial extension
        con.execute("INSTALL spatial; LOAD spatial;")
        print(f"[{datetime.now()}] Spatial extension loaded successfully.")
        
        # Check the total number of rows in the dataset (optional - for progress tracking)
        print(f"[{datetime.now()}] Counting total rows in dataset...")
        total_rows_query = f"""
        SELECT COUNT(*) as total_rows
        FROM read_parquet('{s3_parquet_path}', hive_partitioning=1)
        WHERE year = 2024
        """
        total_rows = con.execute(total_rows_query).fetchone()[0]
        print(f"[{datetime.now()}] Total rows in 2024 dataset: {total_rows:,}")
        
        # Main query logic is now in the export query
        
        # Export to Parquet file
        print(f"[{datetime.now()}] Saving to {output_file}...")
        
        # --- THE FIX IS HERE ---
        # Removed the `hive_partitioning=1` parameter, as it's not needed
        # inside the COPY command's subquery and was causing the parser error.
        export_query = f"""
        COPY (
            SELECT *
            FROM read_parquet('{s3_parquet_path}')
            WHERE year = 2024
        ) TO '{output_file}' (FORMAT PARQUET, COMPRESSION 'ZSTD');
        """
        
        con.execute(export_query)
        
        # Show file size
        file_size = os.path.getsize(output_file)
        print(f"[{datetime.now()}] File size: {file_size / 1024 / 1024:.2f} MB")
        
        # Show database file size
        db_file_size = os.path.getsize(db_file)
        print(f"[{datetime.now()}] Database file size: {db_file_size / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {str(e)}")
        raise
    finally:
        con.close()
        print(f"[{datetime.now()}] Database connection closed.")
    
    print(f"[{datetime.now()}] Preprocessing completed successfully!")
    print(f"[{datetime.now()}] Generated files:")
    print(f"    - Parquet file: {output_file}")
    print(f"    - Persistent database: {db_file}")

if __name__ == "__main__":
    start_time = time.time()
    
    create_unique_stations_dataset()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n--- Total script execution time: {duration:.2f} seconds ---")