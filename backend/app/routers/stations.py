from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import duckdb
from datetime import datetime, date
from decimal import Decimal
import math # Import the math module for cosine calculation
import logging
import os

#unqiue stations schema:
# start_station_name,
#avg_lat as start_lat,
# avg_lng as start_lng,
# ride_count,
# lat_variance,
# lng_variance,
# last_ride_date
        
# Create a new APIRouter instance for this feature
router = APIRouter(
    prefix="/stations",
    tags=["Stations"], #Tags are used to group related endpoints together in the API documentation.
)

# ---- Helper function to serialize values ----
def serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return f"bytes_data_repr:{value!r}"
    return value

# ---- Database Connection Logic ----
con: duckdb.DuckDBPyConnection = None

@router.on_event("startup")
def startup_event():
    
    # Now reads from the pre-processed local file instead of S3.
    global con
    print("Stations Router: Initializing DuckDB connection...")
    con = duckdb.connect(database=':memory:', read_only=False)
    con.execute("INSTALL spatial;")
    con.execute("LOAD spatial;")
    
    # Define the path to your local data file.
    
    local_parquet_path = "backend/app/data/unique_stations.parquet"
    
    if not os.path.exists(local_parquet_path):
        print(f"FATAL ERROR: Optimized data file not found at '{local_parquet_path}'.")
        print("Please run the 'preprocess_data.py' script first.")
        con = None # Set con to None so endpoints will report an error
        return

    try:
        
        print(f"Reading from local file: '{local_parquet_path}'...")
        
        # Create the in-memory table from our small, local, optimized file.
       
        con.execute(f"CREATE TABLE stations AS SELECT * FROM read_parquet('{local_parquet_path}');")
        
        station_count = con.execute("SELECT COUNT(*) FROM stations;").fetchone()[0]
        print(f"Stations Router: Successfully loaded {station_count} unique stations into memory.")
    except Exception as e:
        print(f"FATAL: Could not load data at startup. Error: {e}")
        con = None





@router.on_event("shutdown")
def shutdown_close_db_connection():
    global con
    if con:
        print("Stations Router: Closing DuckDB connection.")
        con.close()




@router.get("/nearest", response_model=List[Dict[str, Any]])
async def get_nearest_stations(lat: float, lon: float, count: int = 5):
    if not con:
        raise HTTPException(status_code=503, detail="Database not available. Check startup logs for errors.")
    
    try:
        print(f"DEBUG: Query params - lat: {lat}, lon: {lon}, count: {count}")
        
        sql_query = """
        SELECT 
            start_station_name, 
            start_lat, 
            start_lng,
            ride_count,
            ST_Distance_Spheroid(
                ST_Point(start_lng,start_lat), 
                ST_Point(?, ?) -- click point lon, lat
            ) AS distance_in_meters
        FROM stations 
        ORDER BY distance_in_meters 
        LIMIT ?;
        """
        params = [lon, lat, count]
        print(f"DEBUG: About to execute query with params: {params}")
        
        result_tuples = con.execute(sql_query, params).fetchall()
        print(f"DEBUG: Query executed successfully, got {len(result_tuples)} results")
        print(f"DEBUG: Raw result_tuples data: {result_tuples}")
        
        # Process the results and convert to proper format
        stations = []
        for row in result_tuples:
            station_data = {
                "start_station_name": serialize_value(row[0]),
                "start_lat": serialize_value(row[1]),
                "start_lng": serialize_value(row[2]),
                "ride_count": serialize_value(row[3]),
                "distance_in_meters": serialize_value(row[4])
            }
            stations.append(station_data)
        
        print(f"DEBUG: Processed {len(stations)} stations for return")
        return stations
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {type(e).__name__}: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "Error during spatial query.", "detail": str(e)})