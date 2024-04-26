import pandas as pd
import pyodbc
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

url = "https://api-nba-v1.p.rapidapi.com/teams"

host = os.getenv("API_HOST")
key = os.getenv("API_KEY")

headers = {
    'x-rapidapi-host': host,
    'x-rapidapi-key': key
}

# Make the API request
response = requests.request("GET", url, headers=headers, params={"season": "2023", "country": "USA"})

# Check if request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()['response']  # Accessing 'response' key

    # Connect to your Azure SQL Server database
    server_name = 'nba-streaming-server.database.windows.net'  # Change with project reviewer's azure sql server name
    database_name = 'nbastreaming'             # Change with project reviewer's azure sql db name
    table_name = 'NBATEAMS'  
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")

    # Connect to SQL Server database
    conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Check if table exists, create it if not
    if not cursor.tables(table=table_name).fetchone():
        cursor.execute(f"CREATE TABLE {table_name} (id INT, name NVARCHAR(255), code NVARCHAR(10), "
                       "city NVARCHAR(255), logo NVARCHAR(255), allStar BIT, nbaFranchise BIT)")

    # Insert data into the table
    for team in data:
        if team['nbaFranchise']:
            cursor.execute(f"INSERT INTO {table_name} (id, name, code, city, logo, allStar, nbaFranchise) "
                           "VALUES (?, ?, ?, ?, ?, ?, ?)",
                           [team['id'], team['name'], team['code'], team['city'], 
                            team['logo'], team['allStar'], team['nbaFranchise']])
    
    # Commit changes
    conn.commit()
    
    print("Data inserted into SQL Server database successfully!")

    # Close the connection
    conn.close()
else:
    print(f"Error: {response.status_code}")
