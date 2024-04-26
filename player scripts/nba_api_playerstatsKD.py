import requests
import pyodbc
from dotenv import load_dotenv
import os 

# Load environment variables from .env file
load_dotenv()

# Setup the API URL and parameters
url = "https://api-nba-v1.p.rapidapi.com/players/statistics" 
host = os.getenv("API_HOST")
key = os.getenv("API_KEY")
player_id = 153
headers = {
    'x-rapidapi-host': host,
    'x-rapidapi-key': key
}
params = {"id": player_id, "season": "2023"}

# Database credentials
server_name = 'nba-streaming-server.database.windows.net'  # Change with project reviewer's azure sql server name
database_name = 'nbastreaming'                         # Change with project reviewer's azure sql db name
username = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
driver = '{ODBC Driver 18 for SQL Server}'
connection_string = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}"
cnxn = pyodbc.connect(connection_string)


# Make the API request
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    player_stats_data = response.json().get('response', [])
    
    # Create a cursor to execute SQL queries
    cursor = cnxn.cursor()

    # Define the table for player stats
    player_stats_table = 'PLAYERSTATS_KD'
    cursor.execute(f'''
    IF OBJECT_ID('{player_stats_table}', 'U') IS NULL
    BEGIN
        CREATE TABLE {player_stats_table} (
            PlayerID INT,
            PlayerFirstName VARCHAR(50),
            PlayerLastName VARCHAR(50),
            TeamID INT,
            TeamName VARCHAR(100),
            TeamNickname VARCHAR(50),
            TeamCode VARCHAR(10),
            TeamLogo VARCHAR(255),
            GameDate DATETIME,  
            Points INT,
            Position VARCHAR(10),
            Minutes VARCHAR(5),
            FGM INT,
            FGA INT,
            FGPercentage FLOAT,
            FTM INT,
            FTA INT,
            FTPercentage FLOAT,
            TPM INT,
            TPA INT,
            TPPercentage FLOAT,
            OffensiveRebounds INT,
            DefensiveRebounds INT,
            TotalRebounds INT,
            Assists INT,
            PersonalFouls INT,
            Steals INT,
            Turnovers INT,
            Blocks INT,
            PlusMinus VARCHAR(5),
            Comment VARCHAR(255)
        )
        PRINT 'Table created successfully.'
    END''')

    # Insert data into the database
    for player_stat in player_stats_data:
        if player_stat.get('player', {}).get('id') == player_id:

            # Retrieves StartDate from NBA_GAMES2023 table
            game_id = player_stat.get('game', {}).get('id')
            cursor.execute("SELECT DateStart FROM NBA_GAMES2023 WHERE Id = ?", (int(game_id),))
            start_date_row = cursor.fetchone()
            game_date = start_date_row[0] if start_date_row else None
            
            # Convert game_date to the appropriate format
            game_date_formatted = game_date.strftime("%Y-%m-%d %H:%M:%S") if game_date else None

            # Check if the row already exists based on PlayerID and GameDate
            cursor.execute(f'''
                SELECT COUNT(*) 
                FROM {player_stats_table} 
                WHERE PlayerID = ? AND GameDate = ?
            ''', (
                player_stat.get('player', {}).get('id'),
                game_date_formatted
            ))
            existing_rows = cursor.fetchone()[0]

            if existing_rows == 0:
                # Row doesn't exist, insert the data
                cursor.execute(f'''INSERT INTO {player_stats_table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    player_stat.get('player', {}).get('id'),
                    player_stat.get('player', {}).get('firstname'),
                    player_stat.get('player', {}).get('lastname'),
                    player_stat.get('team', {}).get('id'),
                    player_stat.get('team', {}).get('name'),
                    player_stat.get('team', {}).get('nickname'),
                    player_stat.get('team', {}).get('code'),
                    player_stat.get('team', {}).get('logo'),
                    game_date_formatted, 
                    player_stat.get('points'),
                    player_stat.get('pos'),
                    player_stat.get('min'),
                    player_stat.get('fgm'),
                    player_stat.get('fga'),
                    player_stat.get('fgp'),
                    player_stat.get('ftm'),
                    player_stat.get('fta'),
                    player_stat.get('ftp'),
                    player_stat.get('tpm'),
                    player_stat.get('tpa'),
                    player_stat.get('tpp'),
                    player_stat.get('offReb'),
                    player_stat.get('defReb'),
                    player_stat.get('totReb'),
                    player_stat.get('assists'),
                    player_stat.get('pFouls'),
                    player_stat.get('steals'),
                    player_stat.get('turnovers'),
                    player_stat.get('blocks'),
                    player_stat.get('plusMinus'),
                    player_stat.get('comment')
                ))
                cnxn.commit()
            else:
                print("Row already exists, skipping insertion.")

    print("All data inserted successfully.")
else:
    print("Failed to retrieve games. Status code:", response.status_code)


cnxn.close()
