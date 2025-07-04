from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

# Create DB on first run
def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        """)

init_db()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/quiz')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        with sqlite3.connect("users.db") as conn:
            try:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                return redirect('/login')
            except sqlite3.IntegrityError:
                return "Username already exists. <a href='/register'>Try again</a>"
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, password FROM users WHERE username = ?", (username,))
            user = cur.fetchone()
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                return redirect('/quiz')
            return "Invalid credentials. <a href='/login'>Try again</a>"

    return render_template("login.html")

@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        return redirect('/login')

    # Fetch username
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
        user = cur.fetchone()
        if user:
            return render_template("quiz.html", username=user[0])
        else:
            return redirect('/logout')  # fallback if user not found

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
