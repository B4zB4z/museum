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
            num_people INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        # Create Feedback table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            feedback_text TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        conn.commit()

@app.route('/')
def index():
    logged_in = 'user_id' in session
    return render_template('museum.html', logged_in=logged_in)  # Render the main museum page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        # Compare plain-text password
        if user and user['password'] == password:
            session['user_id'] = user['id']
            return redirect('/')
        return "Invalid email or password.", 401

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        phone = request.form['phone']
        date_of_birth = request.form['date_of_birth']
        password = request.form['password']  # Store the password directly

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (email, name, phone, date_of_birth, password)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, name, phone, date_of_birth, password))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered. Please try again with a different email.", 400

    return render_template('register.html')


@app.route('/book_tour', methods=['GET', 'POST'])
def book_tour():
    logged_in = 'user_id' in session
    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect('/login')  # Redirect to login if not logged in

        tour_date = request.form['tour_date']
        num_people = request.form['num_people']
        user_id = session['user_id']


        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tours (user_id, tour_date, num_people) VALUES (?, ?, ?)", (user_id, tour_date, num_people))
            conn.commit()
            return redirect('/')  # Redirect to the home page after booking

    return render_template('book_tour.html', logged_in=logged_in)


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    logged_in = 'user_id' in session
    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect('/login')

        feedback_text = request.form.get('feedback')
        user_id = session['user_id']

        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Feedback (user_id, feedback_text)
                VALUES (?, ?)
            """, (user_id, feedback_text))
            conn.commit()
            

    with sqlite3.connect("data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT users.name, feedback_text, submitted_at 
            FROM Feedback 
            JOIN users ON Feedback.user_id = users.id 
            ORDER BY submitted_at DESC
        """)
        feedback_entries = cursor.fetchall()
    return render_template('feedback.html', logged_in=logged_in,feedback_entries=feedback_entries)

@app.route('/contact')
def contact():
    logged_in = 'user_id' in session  # Check if user is logged in
    return render_template('contact.html', logged_in=logged_in)

if __name__ == '__main__':
    init_db()  # Initialize the database and create tables if they don't exist
    app.run(debug=True)
