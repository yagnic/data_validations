import streamlit as st
import pandas as pd
import sqlite3
from hashlib import sha256
import os

# Secure hash function for passwords
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
        # Create feedback table
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, username TEXT, old_question TEXT, new_question TEXT, feedback TEXT)''')
    # Insert default user credentials if not exist
    default_username = 'admin'
    default_password = hash_password('admin123')
    c.execute('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', (default_username, default_password))
    # Insert default feedback viewer credentials
    viewer_username = 'viewer'
    viewer_password = hash_password('viewer123')
    c.execute('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', (viewer_username, viewer_password))
    conn.commit()
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
    c.execute('INSERT INTO feedback (question_id, username, old_question, new_question, feedback) VALUES (?, ?, ?, ?, ?)', (question_id, username, old_question, new_question, feedback))
    conn.commit()
    conn.close()

# Update feedback
def update_feedback(feedback_id, feedback):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('UPDATE feedback SET feedback = ? WHERE id = ?', (feedback, feedback_id))
    conn.commit()
    conn.close()

# Delete feedback
def delete_feedback(feedback_id):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
    conn.commit()
    conn.close()

# Load questions from Excel file
def load_questions():
    df = pd.read_excel('questions.xlsx')
    return df

# Load feedback from database
def load_feedback(limit, offset):
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('SELECT * FROM feedback LIMIT ? OFFSET ?', (limit, offset))
    feedback_data = c.fetchall()
    conn.close()
    return feedback_data

# Get total number of feedback entries
def get_feedback_count():
    conn = sqlite3.connect('users_feedback.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM feedback')
    count = c.fetchone()[0]
    conn.close()
    return count

# Initialize the database
init_db()

# Streamlit app
st.title("Secure Question Feedback System")

# User Authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
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

    if st.session_state.username == 'viewer':
        # View and Manage Feedback Page with Pagination
        st.title("Manage Submitted Feedback")
        feedback_count = get_feedback_count()
        feedback_per_page = 1
        total_pages = (feedback_count // feedback_per_page) + (1 if feedback_count % feedback_per_page > 0 else 0)
        page_number = st.number_input("Page Number", min_value=1, max_value=total_pages, step=1)
        offset = (page_number - 1) * feedback_per_page
        feedback_data = load_feedback(feedback_per_page, offset)

        if feedback_data:
            for entry in feedback_data:
                st.write("---")
                st.write(f"**Feedback ID:** {entry[0]}")
                st.write(f"**Question ID:** {entry[1]}")
                st.write(f"**Submitted by:** {entry[2]}")
                st.write(f"**Old Question:** {entry[3]}")
                st.write(f"**New Question:** {entry[4]}")
                st.write(f"**Feedback:** {entry[5]}")

                # Update Feedback
                new_feedback = st.text_area(f"Update Feedback (ID: {entry[0]})", value=entry[5])
                if st.button(f"Update Feedback {entry[0]}"):
                    update_feedback(entry[0], new_feedback)
                    st.success(f"Feedback ID {entry[0]} updated successfully")

                # Delete Feedback
                if st.button(f"Delete Feedback {entry[0]}"):
                    delete_feedback(entry[0])
                    st.warning(f"Feedback ID {entry[0]} deleted successfully")
        else:
            st.write("No feedback available.")
    else:
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
                st.write(f"**Q:** {old_question.replace('. ', '.\n')}")
            with col2:
                st.write("### New Question:")
                st.write(f"**Q:** {new_question.replace('. ', '.\n')}")

            # Feedback Section
            st.write("### Provide Your Feedback:")
            feedback = st.text_area("Your Feedback")
            if st.button("Submit Feedback"):
                save_feedback(question_idx, st.session_state.username, old_question, new_question, feedback)
                st.success("Feedback submitted successfully")
        else:
            st.warning("No questions available in the file.")
