import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# --- Flask App Setup ---
app = Flask(
    __name__,
    static_folder=os.path.join('login_system', 'static'),     # custom static path
    template_folder=os.path.join('login_system', 'templates') # custom template path
)
app.secret_key = 'your_secret_key_here'

# --- Upload Config ---
UPLOAD_FOLDER = os.path.join('login_system', 'static', 'user_uploads')  # fixed path
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Helpers ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_username(user_id):
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()
        return result[0] if result else ""

# Initialize database
def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS user_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image_number INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            UNIQUE(user_id, image_number)
        );
        """)

init_db()

# ✅ Only one correct version of get_user_image
def get_user_image(user_id, image_number):
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT image_path FROM user_images WHERE user_id = ? AND image_number = ?", (user_id, image_number))
        result = cur.fetchone()
        if result:
            path = result[0]
            print(f"[Override] {image_number} -> {path}")
            return url_for('static', filename=path)
        else:
            default_jpg = f'images/{image_number}.jpg'
            default_png = f'images/{image_number}.png'
            
            static_dir = os.path.join('login_system', 'static')

            if os.path.exists(os.path.join(static_dir, default_jpg)):
                print(f"[Default JPG] {image_number} -> {default_jpg}")
                return url_for('static', filename=default_jpg)

            if os.path.exists(os.path.join(static_dir, default_png)):
                print(f"[Default PNG] {image_number} -> {default_png}")
                return url_for('static', filename=default_png)

            print(f"[Missing image] {image_number}")
            return url_for('static', filename='images/placeholder.png')


@app.route('/')
def home():
    return redirect('/quiz') if 'user_id' in session else redirect('/login')

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    image_map = {i: get_user_image(user_id, i) for i in range(100)}
    return render_template("quiz.html", image_map=image_map, username=get_username(user_id))

@app.route('/upload_override', methods=['GET', 'POST'])
def upload_override():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        image_number = int(request.form['image_number'])
        file = request.files.get('image')

        if not file or not allowed_file(file.filename):
            flash("Invalid image file.")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        user_id = session['user_id']
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
        os.makedirs(user_folder, exist_ok=True)
        save_path = os.path.join(user_folder, f'{image_number}_{filename}')
        file.save(save_path)

        relative_path = os.path.relpath(save_path, 'static').replace("\\", "/")

        with sqlite3.connect("users.db") as conn:
            conn.execute("""
                INSERT INTO user_images (user_id, image_number, image_path)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, image_number) DO UPDATE SET image_path = excluded.image_path
            """, (user_id, image_number, relative_path))
            conn.commit()

        flash(f"Custom image for number {image_number} uploaded.")
        return redirect(request.url)

    return render_template("upload_override.html")

@app.route('/course')
def course():
    if 'user_id' not in session:
        return redirect('/login')
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
        user = cur.fetchone()
    return render_template("course.html", username=user[0] if user else "")
