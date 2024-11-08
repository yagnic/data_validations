# Flask backend for the Question Feedback System
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
import logging

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS to allow requests from any origin

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Initialize the database

def init_db():
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            old_question TEXT,
            new_question TEXT,
            feedback TEXT,
            updated BOOLEAN DEFAULT 0,
            approved BOOLEAN DEFAULT 0,
            assigned_to TEXT,
            difficulty TEXT,
            editor TEXT
        )
    ''')
    # Create default admin user
    hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    c.execute('''
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES (?, ?, ?)
    ''', ('admin', hashed_password, 'admin'))
    conn.commit()
    conn.close()

init_db()

# Route to get questions assigned to a user
@app.route('/questions/<username>', methods=['GET'])
def get_user_questions(username):
    logging.info(f"Fetching questions for user: {username}")
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    if username == 'admin':
        c.execute('SELECT * FROM questions')
    else:
        c.execute('SELECT * FROM questions WHERE assigned_to = ?', (username,))
    questions = c.fetchall()
    conn.close()
    
    if len(questions) == 0:
        logging.warning(f"No questions found for user: {username}. Check if questions are correctly assigned.")
    else:
        logging.info(f"Questions fetched for user: {username}: {questions}")

    return jsonify([{
        'id': row[0],
        'old_question': row[1],
        'new_question': row[2],
        'feedback': row[3],
        'updated': bool(row[4]),
        'approved': bool(row[5]),
        'assigned_to': row[6],
        'difficulty': row[7] if len(row) > 7 else None,
        'editor': row[8] if len(row) > 8 else None
    } for row in questions])

# Route to edit a question
@app.route('/questions/edit', methods=['POST'])
def edit_question():
    data = request.get_json()
    question_id = data['question_id']
    new_question = data['new_question']
    editor = data['editor']
    difficulty = data['difficulty']
    feedback = data['feedback']
    approval_status = data['approval_status']

    logging.info(f"Editing question ID: {question_id} by editor: {editor}")

    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('''
        UPDATE questions SET new_question = ?, updated = 1, approved = ?, feedback = ?, difficulty = ?, editor = ? WHERE id = ?
    ''', (new_question, 1 if approval_status == 'approved' else 0, feedback, difficulty, editor, question_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Question edited successfully'})

# Route to submit feedback
@app.route('/questions/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    question_id = data['question_id']
    feedback = data['feedback']
    logging.info(f"Submitting feedback for question ID: {question_id}")
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('UPDATE questions SET feedback = ?, updated = 1 WHERE id = ?', (feedback, question_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Feedback submitted successfully'})

# Route to approve a question
@app.route('/questions/approve', methods=['POST'])
def approve_question():
    data = request.get_json()
    question_id = data['question_id']
    logging.info(f"Approving question ID: {question_id}")
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('UPDATE questions SET approved = 1 WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Question approved successfully'})

# Route to handle login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password'].encode('utf-8')
    logging.info(f"Login attempt for username: {username}")
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password, user[2].encode('utf-8')):
        logging.info(f"Login successful for username: {username}")
        return jsonify({'message': 'Login successful', 'username': username, 'role': user[3]})
    else:
        logging.warning(f"Invalid credentials for username: {username}")
        return jsonify({'message': 'Invalid credentials'}), 401

# Route to handle registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password'].encode('utf-8')
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
    role = data.get('role', 'teacher')
    logging.info(f"Registering user: {username} with role: {role}")
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, role))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully'})
    except sqlite3.IntegrityError:
        conn.close()
        logging.warning(f"Username already exists: {username}")
        return jsonify({'message': 'Username already exists'}), 400

# Route to get user ID by username
@app.route('/user-id/<username>', methods=['GET'])
def get_user_id(username):
    logging.info(f"Fetching user ID for username: {username}")
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user:
        logging.info(f"User ID for {username}: {user[0]}")
        return jsonify({'user_id': user[0]})
    else:
        logging.warning(f"User not found for username: {username}")
        return jsonify({'message': 'User not found'}), 404

# Route to get all users for admin to assign questions
@app.route('/users', methods=['GET'])
def get_users():
    logging.info("Fetching users for assignment")
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('SELECT id, username FROM users WHERE role = ?', ('teacher',))
    users = c.fetchall()
    conn.close()
    logging.info("Users fetched successfully")
    return jsonify([{
        'id': row[0],
        'username': row[1]
    } for row in users])

# Route to assign questions to a user
@app.route('/assign-questions', methods=['POST'])
def assign_questions():
    data = request.get_json()
    user_id = data['user_id']
    question_start = data['question_start']
    question_end = data['question_end']
    logging.info(f"Assigning questions from {question_start} to {question_end} to user ID: {user_id}")
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    # Get the username of the user to assign questions to
    c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    if not user:
        logging.error(f"User not found with ID: {user_id}")
        return jsonify({'message': 'User not found'}), 404

    username = user[0]

    # Assign questions to the user
    c.execute('UPDATE questions SET assigned_to = ? WHERE id BETWEEN ? AND ?', (username, question_start, question_end))
    conn.commit()
    conn.close()
    logging.info(f"Questions assigned successfully to {username}")
    return jsonify({'message': 'Questions assigned successfully'})

if __name__ == '__main__':
    app.run(debug=True)
