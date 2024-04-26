import requests
import pyodbc
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Setup the API URL and parameters
url = "https://api-nba-v1.p.rapidapi.com/games"
host = os.getenv("API_HOST")
key = os.getenv("API_KEY")
headers = {
    'x-rapidapi-host': host,
    'x-rapidapi-key': key
}
params = {"season": "2023",}

# Make the API request
response = requests.get(url, headers=headers, params=params)

# Connect to Azure SQL Database
server_name = 'nba-streaming-server.database.windows.net'
database_name = 'nbastreaming'
username = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
table_name = 'NBA_GAMES2023'  
driver = '{ODBC Driver 18 for SQL Server}'
connection_string = f'DRIVER={driver};SERVER={server_name};PORT=1433;DATABASE={database_name};UID={username};PWD={password}'
cnxn = pyodbc.connect(connection_string)

# Check if the request was successful
if response.status_code == 200:
    games_data = response.json().get('response', [])

    # Create a cursor to execute SQL queries
    cursor = cnxn.cursor()

    # Insert data into the database
    for index, game in enumerate(games_data):

        # Check if the game already exists in the database
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE Id = ?", (game.get('id'),))
        existing_rows = cursor.fetchone()[0]

        if existing_rows == 0:
            cursor.execute(f'''INSERT INTO {table_name} (
                                Id, League, Season, DateStart, DateEnd, Duration, Stage, StatusClock, 
                                StatusHalftime, StatusShort, StatusLong, PeriodsCurrent, PeriodsTotal, 
                                PeriodsEndOfPeriod, ArenaName, ArenaCity, ArenaState, ArenaCountry, 
                                VisitorTeam, HomeTeam, VisitorWin, VisitorLoss, VisitorPoints, HomeWin, 
                                HomeLoss, HomePoints, TimesTied, LeadChanges
                              ) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (game.get('id'),
                            game.get('league'),
                            game.get('season'),
                            game.get('date', {}).get('start'),
                            game.get('date', {}).get('end') or None,
                            game.get('date', {}).get('duration') or None,
                            game.get('stage'),
                            game.get('status', {}).get('clock') or None,
                            game.get('status', {}).get('halftime') or False,
                            game.get('status', {}).get('short') or None,
                            game.get('status', {}).get('long') or None,
                            game.get('periods', {}).get('current') or None,
                            game.get('periods', {}).get('total') or None,
                            game.get('periods', {}).get('endOfPeriod') or False,
                            game.get('arena', {}).get('name') or None,
                            game.get('arena', {}).get('city') or None,
                            game.get('arena', {}).get('state') or None,
                            game.get('arena', {}).get('country') or None,
                            game.get('teams', {}).get('visitors', {}).get('name') or None,
                            game.get('teams', {}).get('home', {}).get('name') or None,
                            game.get('teams', {}).get('visitors', {}).get('win') or None,
                            game.get('teams', {}).get('visitors', {}).get('loss') or None,
                            game.get('teams', {}).get('visitors', {}).get('linescore', {}).get('points') or None,
                            game.get('teams', {}).get('home', {}).get('win') or None,
                            game.get('teams', {}).get('home', {}).get('loss') or None,
                            game.get('teams', {}).get('home', {}).get('linescore', {}).get('points') or None,
                            game.get('timesTied') or None,
                            game.get('leadChanges') or None))

            # Commit changes to the database
            cnxn.commit()

else:
    print("Failed to retrieve games. Status code:", response.status_code)

# Close the database connection
cnxn.close()
