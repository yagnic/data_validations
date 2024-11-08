import pandas as pd
import sqlite3

# Load data from Excel
def load_data_from_excel():
    # Load questions from questions.xlsx
    df = pd.read_excel('questions.xlsx')
    return df

# Insert data into SQLite database
def insert_data_into_db(dataframe):
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()

    # Create the questions table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            old_question TEXT,
            new_question TEXT,
            feedback TEXT DEFAULT '',
            updated BOOLEAN DEFAULT 0,
            approved BOOLEAN DEFAULT 0
        )
    ''')

    # Insert data from the dataframe into the questions table
    for _, row in dataframe.iterrows():
        cursor.execute('''
            INSERT INTO questions (old_question, new_question) VALUES (?, ?)
        ''', (row['old_questions'], row['new_questions']))

    # Commit changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Load the data from the Excel file
    data = load_data_from_excel()

    # Insert the data into the SQLite database
    insert_data_into_db(data)
    print("Data from questions.xlsx has been successfully inserted into questions.db.")
