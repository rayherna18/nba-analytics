import requests
import pyodbc
from dotenv import load_dotenv
import os 

# Load environment variables from .env file
load_dotenv()


url = "https://api-nba-v1.p.rapidapi.com/teams/statistics"  
host = os.getenv("API_HOST")
key = os.getenv("API_KEY")
# Team ID's for Lakers, Bulls, Warriors, Celtics and Cavaliers.
team_ids = [6, 7, 11, 14, 17]  
headers = {
    'x-rapidapi-host': host,
    'x-rapidapi-key': key
}

server_name = 'nba-streaming-server.database.windows.net'
database_name = 'nbastreaming'
table_name = 'TEAMSTATS'
username = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
driver = '{ODBC Driver 18 for SQL Server}'
connection_string = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}"
cnxn = pyodbc.connect(connection_string)

# Create a cursor to execute SQL queries
cursor = cnxn.cursor()

# Check if the table exists, if not, create it
cursor.execute(f'''IF OBJECT_ID('dbo.{table_name}', 'U') IS NULL
                    CREATE TABLE dbo.{table_name} (
                        TeamID INT,
                        Games INT,
                        FastBreakPoints INT,
                        PointsInPaint INT,
                        BiggestLead INT,
                        SecondChancePoints INT,
                        PointsOffTurnovers INT,
                        LongestRun INT,
                        Points INT,
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
                        PlusMinus INT
                    )''')

# Iterate over team IDs
for team_id in team_ids:
    # Make the API request
    response = requests.get(url, headers=headers, params={"id": team_id, "season": "2023"})

    # Check if the request was successful
    if response.status_code == 200:
        team_stats_data = response.json().get('response', [])

        # Insert data into the database
        for team_stats in team_stats_data:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE TeamID = ?", (team_id,))
            existing_rows = cursor.fetchone()[0]

            if existing_rows == 0:
                cursor.execute(f'''INSERT INTO dbo.{table_name} (
                                        TeamID, Games, FastBreakPoints, PointsInPaint, BiggestLead,
                                        SecondChancePoints, PointsOffTurnovers, LongestRun, Points, 
                                        FGM, FGA, FGPercentage, FTM, FTA, FTPercentage, TPM, TPA, 
                                        TPPercentage, OffensiveRebounds, DefensiveRebounds, TotalRebounds, 
                                        Assists, PersonalFouls, Steals, Turnovers, Blocks, PlusMinus
                                      ) 
                                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (team_id,
                                team_stats.get('games'),
                                team_stats.get('fastBreakPoints'),
                                team_stats.get('pointsInPaint'),
                                team_stats.get('biggestLead'),
                                team_stats.get('secondChancePoints'),
                                team_stats.get('pointsOffTurnovers'),
                                team_stats.get('longestRun'),
                                team_stats.get('points'),
                                team_stats.get('fgm'),
                                team_stats.get('fga'),
                                team_stats.get('fgp'),
                                team_stats.get('ftm'),
                                team_stats.get('fta'),
                                team_stats.get('ftp'),
                                team_stats.get('tpm'),
                                team_stats.get('tpa'),
                                team_stats.get('tpp'),
                                team_stats.get('offReb'),
                                team_stats.get('defReb'),
                                team_stats.get('totReb'),
                                team_stats.get('assists'),
                                team_stats.get('pFouls'),
                                team_stats.get('steals'),
                                team_stats.get('turnovers'),
                                team_stats.get('blocks'),
                                team_stats.get('plusMinus')))

                # Commit changes to the database
                cnxn.commit()
            else:
                print("Data for Team ID", team_id, "already exists in the database. Skipping insertion.")
    else:
        print("Failed to retrieve team statistics for Team ID:", team_id, "Status code:", response.status_code)

cnxn.close()
