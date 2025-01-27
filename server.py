import sqlite3
from flask import Flask, request, jsonify, session, redirect, render_template, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
CORS(app)

# Initialize the database
def init_db():
    with sqlite3.connect("data.db") as conn:
        cursor = conn.cursor()
        # Create Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            password TEXT NOT NULL
        )
        """)
        # Create Tours table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tour_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        # Create Feedback table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            feedback_text TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        conn.commit()

@app.route('/')
def index():
    return render_template('museum.html')  # Render the main museum page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect('/')
        return "Invalid email or password.", 401

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        phone = request.form['phone']
        date_of_birth = request.form['date_of_birth']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (email, name, phone, date_of_birth, password)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, name, phone, date_of_birth, hashed_password))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered. Please try again with a different email.", 400

    return render_template('register.html')

@app.route('/book-tour', methods=['POST'])
def book_tour():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.json
    tour_date = data.get('tour_date')
    user_id = session['user_id']

    with sqlite3.connect("data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Tours (user_id, tour_date) VALUES (?, ?)", (user_id, tour_date))
        conn.commit()
        return jsonify({"message": "Tour booked successfully"}), 201

@app.route('/feedback', methods=['POST'])
def feedback():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.json
    feedback_text = data.get('feedback')
    user_id = session['user_id']

    with sqlite3.connect("data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Feedback (user_id, feedback_text) VALUES (?, ?)", (user_id, feedback_text))
        conn.commit()
        return jsonify({"message": "Feedback submitted successfully"}), 201

if __name__ == '__main__':
    init_db()  # Initialize the database and create tables if they don't exist
    app.run(debug=True)
