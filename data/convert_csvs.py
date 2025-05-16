import os
import sqlite3
import pandas as pd

def create_database_from_csvs(csv_directory, database_name):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    # Iterate through all CSV files in the directory
    for file_name in os.listdir(csv_directory):
        if file_name.endswith('.csv'):
            file_path = os.path.join(csv_directory, file_name)
            table_name = os.path.splitext(file_name)[0]  # Use file name (without extension) as table name

            # Read the CSV file into a Pandas DataFrame
            df = pd.read_csv(file_path, sep=';', encoding='utf-8')

            # Replace spaces in column names with underscores for SQLite compatibility
            df.columns = [col.replace(' ', '_') for col in df.columns]

            # Create table schema based on DataFrame columns
            df.to_sql(table_name, conn, if_exists='replace', index=False)

            print(f"Table '{table_name}' created/updated in the database.")

    # Close the database connection
    conn.close()

if __name__ == "__main__":
    # Define the directory containing the CSV files and the SQLite database name
    csv_directory = "./raw/Primaerdaten"
    database_name = "primaerdaten.db"

    # Create the SQLite database from the CSV files
    create_database_from_csvs(csv_directory, database_name)
    print(f"Database '{database_name}' has been created successfully.")