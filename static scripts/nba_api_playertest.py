import pyodbc
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

url = "https://api-nba-v1.p.rapidapi.com/players"
host = os.getenv("API_HOST")
key = os.getenv("API_KEY")

headers = {
    'x-rapidapi-host': host,
    'x-rapidapi-key': key
}

# Make the API request
response = requests.request("GET", url, headers=headers, params={"season": "2023", "country": 'USA'})

# Check if request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()['response']  # Accessing 'response' key

    if data:
        for player in data:
            print("Player ID:", player['id'])
            print("Name:", player['firstname'], player['lastname'])
            print("Birth Date:", player['birth']['date'])
            print("Birth Country:", player['birth']['country'])
            print("NBA Start:", player['nba']['start'])
            print("NBA Pro Years:", player['nba']['pro'])
            print("Height:", player['height']['feets'], "feet", player['height']['inches'], "inches")
            print("Height (Meters):", player['height']['meters'])
            print("Weight:", player['weight']['pounds'], "pounds", player['weight']['kilograms'], "kilograms")
            print("College:", player['college'])
            print("Affiliation:", player['affiliation'])
            print("\n")

    # Connect to your Azure SQL Server database
    server_name = 'nba-streaming-server.database.windows.net'
    database_name = 'nbastreaming'
    table_name = 'NBA_PLAYERS'  
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")

    # Connect to SQL Server database
    conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Check if table exists, create it if not
    if not cursor.tables(table=table_name).fetchone():
        cursor.execute(f"CREATE TABLE {table_name} (id INT, firstname NVARCHAR(255), lastname NVARCHAR(255), "
                       "birth_date DATE, birth_country NVARCHAR(255), nba_start INT, nba_pro_years INT, "
                       "height_feet INT, height_inches INT, height_meters FLOAT, weight_pounds INT, "
                       "weight_kilograms FLOAT, college NVARCHAR(255), affiliation NVARCHAR(255))")

    # Insert data into the table
    for player in data:
        cursor.execute(f"INSERT INTO {table_name} (id, firstname, lastname, birth_date, birth_country, "
                       "nba_start, nba_pro_years, height_feet, height_inches, height_meters, weight_pounds, "
                       "weight_kilograms, college, affiliation) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       [player['id'], player['firstname'], player['lastname'], player['birth']['date'], 
                        player['birth']['country'], player['nba']['start'], player['nba']['pro'], 
                        player['height']['feets'], player['height']['inches'], player['height']['meters'], 
                        player['weight']['pounds'], player['weight']['kilograms'], player['college'], 
                        player['affiliation']])
    
    # Commit changes
    conn.commit()
    
    print("Data inserted into SQL Server database successfully!")

    # Close the connection
    conn.close()
else:
    print(f"Error: {response.status_code}")
