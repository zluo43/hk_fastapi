from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union, List, Dict, Any
import duckdb
import json
from decimal import Decimal
from datetime import datetime, date

app = FastAPI(title="FastAPI Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:8001"],  # React default port and server port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def serialize_value(value):
    """Convert non-serializable values to JSON-serializable format"""
    if isinstance(value, (datetime, date)):
        return value.isoformat()  #covnert to string ISO 8601 format for date and datetime
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return str(value)  # Convert to string representation
    elif value is None:
        return None
    else:
        return value

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

@app.get("/about")
async def about():
    return {"message": "About page"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "message": f"I bought this item with Item ID: {item_id}"}

@app.get("/s3-parquet-sample/", response_model=List[Dict[str, Any]])
async def get_s3_parquet_sample():
    s3_parquet_path = "s3://us-west-2.opendata.source.coop/zluo43/citibike/new_schema_combined_with_geom.parquet/**/*.parquet"
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        con.execute("""INSTALL SPATIAL""")
        con.execute("""LOAD 'spatial'""")

        query = f"SELECT * FROM read_parquet('{s3_parquet_path}') WHERE year=2024 LIMIT 5;"

        # Execute the query and fetch results
        result_relation = con.execute(query)
        
        # Get column names
        column_names = [desc[0] for desc in result_relation.description]
        
        # Fetch all rows as a list of tuples
        rows = result_relation.fetchall() #rows will be a python list
        # for row in rows:
        #     for i, value in enumerate(row):
        #         print (i,value)
        #     break

        
        # Convert rows to a list of dictionaries with proper serialization
        data = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                row_dict[column_names[i]] = serialize_value(value)
            data.append(row_dict)
        
        con.close()

        if not data:
            return JSONResponse(status_code=404, content={"message": "No data found"})
        return data
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    

# --- NEW ENDPOINT for Basic Spatial Query ---
@app.get("/nearest-stations/", response_model=List[Dict[str, Any]])
async def get_nearest_stations(lat: float, lon: float, count: int = 5):
    """
    Finds 'count' nearest start stations to the given latitude and longitude.
    Assumes 'start_lat' and 'start_lng' columns exist in the Parquet file.
    If 'start_geom' (WKB) exists, it could be used for more accurate spatial indexing/querying.
    """
    s3_parquet_path = "s3://us-west-2.opendata.source.coop/zluo43/citibike/new_schema_combined_with_geom.parquet/**/*.parquet"
    
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        
        # Ensure httpfs and spatial extensions are available and loaded.
        # These might need to be run only once if an error occurs saying they aren't loaded.
        try:
            con.execute("""INSTALL SPATIAL""")
            con.execute("""LOAD 'spatial'""")
        except duckdb.IOException as e:
            print(f"Could not install/load extensions (possibly already loaded or network issue): {e}")
        except Exception as e: # Catch any other duckdb related error during extension loading
            print(f"An error occurred with DuckDB extensions: {e}")
            # Decide if you want to proceed or return an error. For now, we'll try to proceed.
            sql_query = f"""
        SELECT 
            start_station_name, 
            start_lat, 
            start_lng,
            ST_Distance_Spheroid(
                ST_Point(start_lng, start_lat), 
                ST_Point({lon}, {lat})
            ) AS distance_m 

        FROM read_parquet('{s3_parquet_path}')
        WHERE start_lat IS NOT NULL AND start_lng IS NOT NULL -- Ensure we have valid coordinates
        ORDER BY distance_m
        LIMIT {count};
     
        """
        result_relation = con.execute(sql_query)
        column_names = [desc[0] for desc in result_relation.description]
        rows_tuples = result_relation.fetchall()
        
        data = []
        for row_tuple in rows_tuples:
            row_dict = {}
            for i, value in enumerate(row_tuple):
                row_dict[column_names[i]] = serialize_value(value)
            data.append(row_dict)
            
        con.close()

        if not data:
            return JSONResponse(status_code=404, content={"message": "No nearby stations found or data issue."})
        
        return data
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})