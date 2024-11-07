import streamlit as st
import pandas as pd
import sqlite3
from hashlib import sha256
import os
import datetime

# Secure hash function for passwords
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    # Create feedback table if it doesn't exist, and alter it if needed
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, username TEXT, old_question TEXT, new_question TEXT, feedback TEXT, updated_by TEXT, updated_at TEXT, approved BOOLEAN)''')
    # Add missing columns if they do not exist
    existing_columns = [row[1] for row in c.execute('PRAGMA table_info(feedback)')]
    if 'updated_by' not in existing_columns:
        c.execute('ALTER TABLE feedback ADD COLUMN updated_by TEXT')
    if 'updated_at' not in existing_columns:
        c.execute('ALTER TABLE feedback ADD COLUMN updated_at TEXT')
    if 'approved' not in existing_columns:
        c.execute('ALTER TABLE feedback ADD COLUMN approved BOOLEAN')
    conn.commit()
    conn.close()

# User registration
def register_user(username, password):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    if c.fetchone():
        st.warning('Username already exists')
    else:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        st.success('User registered successfully')
    conn.close()

# User authentication
def login_user(username, password):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result

# Save feedback
def save_feedback(question_id, username, old_question, new_question, feedback):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO feedback (question_id, username, old_question, new_question, feedback, updated_by, updated_at, approved) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
              (question_id, username, old_question, new_question, feedback, username, updated_at, False))
    conn.commit()
    conn.close()

# Update feedback by the same user
def update_feedback_by_user(question_id, username, feedback):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('UPDATE feedback SET feedback = ?, updated_by = ?, updated_at = ? WHERE question_id = ? AND username = ?', (feedback, username, updated_at, question_id, username))
    conn.commit()
    conn.close()

# Delete feedback
def delete_feedback(feedback_id):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
    conn.commit()
    conn.close()

# Approve feedback
def approve_feedback(feedback_id, approved):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('UPDATE feedback SET approved = ? WHERE id = ?', (approved, feedback_id))
    conn.commit()
    conn.close()

# Load questions from Excel file
def load_questions():
    df = pd.read_excel('questions.xlsx')
    return df

# Load feedback for a specific question
def load_feedback_for_question(question_id):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('SELECT * FROM feedback WHERE question_id = ?', (question_id,))
    feedback_data = c.fetchall()
    conn.close()
    return feedback_data

# Load updated questions
def load_updated_questions():
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT question_id FROM feedback WHERE approved = 1')
    updated_questions = [row[0] for row in c.fetchall()]
    conn.close()
    return updated_questions

# Initialize the database
init_db()

# Streamlit app
st.title("Secure Question Feedback System")

# User Authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if not st.session_state.logged_in:
    if choice == "Register":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        if st.button("Register"):
            register_user(new_user, new_password)
    elif choice == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome {username}")
                st.experimental_set_query_params()
            else:
                st.error("Invalid Username or Password")
else:
    st.sidebar.title(f"Welcome {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_set_query_params()

    updated_questions = load_updated_questions()

    st.sidebar.title("Updated Questions")
    if updated_questions:
        selected_updated_question = st.sidebar.selectbox("Select Updated Question", updated_questions)
        if st.sidebar.button("View Updated Question"):
            st.title("Updated Question Details")
            old_question = questions_df.iloc[selected_updated_question]['old_questions']
            new_question = questions_df.iloc[selected_updated_question]['new_questions']
            st.write("### Old Question:")
            st.write(old_question)
            st.write("### New Question:")
            st.write(new_question)
    else:
        st.sidebar.write("No updated questions available.")

    # Load Questions Page
    st.title("Question Feedback Page")
    questions_df = load_questions()

    if not questions_df.empty:
        # Question Navigation
        question_idx = st.number_input("Select Question Number", min_value=0, max_value=len(questions_df)-1, step=1)
        old_question = questions_df.iloc[question_idx]['old_questions']
        new_question = questions_df.iloc[question_idx]['new_questions']

        # Display Questions Side by Side
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Old Question:")
            st.write(old_question)
        with col2:
            st.write("### New Question:")
            st.write(new_question)

        # Feedback Section
        feedbacks = load_feedback_for_question(question_idx)
        if feedbacks:
            latest_feedback = max(feedbacks, key=lambda x: x[7])
            st.write("---")
            st.write(f"**Feedback by {latest_feedback[2]} (Updated at: {latest_feedback[7]}, Approved: {'Yes' if latest_feedback[8] else 'No'})**")
            st.write(latest_feedback[5])

        st.write("### Provide Your Feedback:")
        feedback = st.text_area("Your Feedback", height=100)
        if st.button("Submit Feedback"):
            save_feedback(question_idx, st.session_state.username, old_question, new_question, feedback)
            st.success("Feedback submitted successfully")

        # Update Feedback by User
        user_feedback = [fb for fb in feedbacks if fb[2] == st.session_state.username]
        if user_feedback:
            st.write("### Update Your Feedback:")
            current_feedback = user_feedback[0][5]
            updated_feedback = st.text_area("Update Your Feedback", value=current_feedback, height=100)
            if st.button("Update Feedback"):
                update_feedback_by_user(question_idx, st.session_state.username, updated_feedback)
                st.success("Your feedback has been updated successfully.")

    else:
        st.warning("No questions available in the file.")

    # Show Approved Updates below the questions
    if updated_questions:
        st.write("### Approved Updates")
        for uq in updated_questions:
            old_question = questions_df.iloc[uq]['old_questions']
            new_question = questions_df.iloc[uq]['new_questions']
            st.write(f"**Updated Question ID:** {uq}")
            st.write("**Old Question:")
            st.write(old_question)
            st.write("**New Question:**")
            st.write(new_question)
            st.write("---")
    else:
        st.write("No approved updates available.")
