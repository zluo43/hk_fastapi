from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import duckdb
from datetime import datetime, date
from decimal import Decimal
import math # Import the math module for cosine calculation

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

# @router.on_event("startup")
# def startup_load_stations():
#     global con
#     print("Stations Router: Initializing DuckDB and loading data...")
#     s3_parquet_path = "s3://us-west-2.opendata.source.coop/zluo43/citibike/new_schema_combined_with_geom.parquet/**/*.parquet"
#     con = duckdb.connect(database=':memory:', read_only=False)
#     try:
#         con.execute("INSTALL spatial;")
#         con.execute("LOAD spatial;")
#         print("Reading from S3 and creating in-memory 'stations' table...")
#         con.execute(f"""
#             CREATE TABLE stations AS 
#             SELECT * FROM read_parquet('{s3_parquet_path}',hive_partitioning=1)
#             WHERE year=2025
#             LIMIT 100000
#         """)
#         station_count = con.execute("SELECT COUNT(*) FROM stations;").fetchone()[0]
#         print(f"Stations Router: Loaded {station_count} rows into memory.")
#     except Exception as e:
#         print(f"FATAL: Stations Router could not load data. Error: {e}")
#         con = None



#Try no data table creation start up
@router.on_event("startup")
def startup_event():
    # --- MODIFIED STARTUP ---
    # We now only create the connection and load the extension.
    # We DO NOT load the data into memory.
    global con
    print("Stations Router: Initializing DuckDB connection...")
    con = duckdb.connect(database=':memory:', read_only=False)
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
        print("Stations Router: Spatial extension loaded.")
    except Exception as e:
        print(f"FATAL: Could not load spatial extension. Error: {e}")
        con = None

@router.on_event("shutdown")
def shutdown_close_db_connection():
    global con
    if con:
        print("Stations Router: Closing DuckDB connection.")
        con.close()

# ---- Endpoints ----

#Now the path becomes URL:.../stations/nearest
@router.get("/nearest", response_model=List[Dict[str, Any]])
async def get_nearest_stations(lat: float, lon: float, count: int = 5, year: int = 2025):
    if not con:
        raise HTTPException(status_code=503, detail="Database not available.")
    
    # S3 path is now defined here, as it's used in every query
    s3_parquet_path = "s3://us-west-2.opendata.source.coop/zluo43/citibike/new_schema_combined_with_geom.parquet/**/*.parquet"
    
    try:
        # Calculate search bounding box (same as before)
        search_radius_m = 2000
        lat_degree_in_m = 111132
        lng_degree_in_m = lat_degree_in_m * math.cos(math.radians(lat))
        lat_delta = search_radius_m / lat_degree_in_m
        lon_delta = search_radius_m / lng_degree_in_m
        search_bbox = {
            "xmin": lon - lon_delta, "xmax": lon + lon_delta,
            "ymin": lat - lat_delta, "ymax": lat + lat_delta
        }

        # --- MODIFIED QUERY ---
        # This query now reads directly from S3 on every call.
        # It includes both the bbox filter AND the unique station name optimization.
        sql_query = """
        WITH station_rides AS (
            SELECT *
            FROM read_parquet(?, hive_partitioning=1)
            WHERE 
                -- Fast Bbox Intersection filter
                year=?
                AND
                start_geom_bbox.xmin <= ? AND -- search_bbox.xmax
                start_geom_bbox.xmax >= ? AND -- search_bbox.xmin
                start_geom_bbox.ymin <= ? AND -- search_bbox.ymax
                start_geom_bbox.ymax >= ?     -- search_bbox.ymin
                
               

        ),
        unique_stations AS (
            -- Find the first occurrence of each unique station within the candidates
            -- to prevent calculating distance to the same station hundreds of times.
            SELECT *
            FROM station_rides
            QUALIFY ROW_NUMBER() OVER(PARTITION BY start_station_name ORDER BY started_at DESC) = 1.  --arbitrary most recent ride to temporaril represent the correct location 
        )
        SELECT 
            start_station_name, 
            start_lat, 
            start_lng,
            ST_Distance_Spheroid(
                ST_Point(start_lng, start_lat), 
                ST_Point(?, ?) -- click point lon, lat
            ) AS distance_in_meters
        FROM unique_stations 
        ORDER BY distance_in_meters ASC
        LIMIT ?;
        """
        params = [
            s3_parquet_path,
            year,
            search_bbox["xmax"], search_bbox["xmin"],
            search_bbox["ymax"], search_bbox["ymin"],
            lon, lat,
            count
        ]
        
        result_tuples = con.execute(sql_query, params).fetchall()
        
        if not result_tuples:
            return JSONResponse(status_code=404, content={"message": "No nearby stations found within the search radius."})
            
        data = [{"start_station_name": str(r[0]), "start_lat": float(r[1]), "start_lng": float(r[2]), "distance_in_meters": float(r[3])} for r in result_tuples]
        return data
    except duckdb.Error as e:
        return JSONResponse(status_code=500, content={"message": "Error during spatial query.", "detail": str(e)})

