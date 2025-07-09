import os
import random
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# --- Flask Setup ---
app = Flask(
    __name__,
    static_folder=os.path.join('login_system', 'static'),
    template_folder=os.path.join('login_system', 'templates')
)
app.secret_key = os.environ.get("SECRET_KEY", "default_dev_secret")

# --- Config ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///users.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join('login_system', 'static', 'user_uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class UserImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_number = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String(300), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'image_number'),)

# --- Auto-create Tables on First Request ---
@app.before_first_request
def create_tables():
    db.create_all()

# --- Helpers ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_username(user_id):
    user = db.session.get(User, user_id)
    return user.username if user else ""

def get_user_image(user_id, image_number):
    entry = UserImage.query.filter_by(user_id=user_id, image_number=image_number).first()
    if entry:
        print(f"[Override] {image_number} -> {entry.image_path}")
        return url_for('static', filename=entry.image_path)

    default_jpg = f'images/{image_number}.jpg'
    default_png = f'images/{image_number}.png'
    static_dir = os.path.join('login_system', 'static')

    if os.path.exists(os.path.join(static_dir, default_jpg)):
        return url_for('static', filename=default_jpg)
    if os.path.exists(os.path.join(static_dir, default_png)):
        return url_for('static', filename=default_png)

    return url_for('static', filename='images/placeholder.png')

# --- Routes ---
@app.route('/')
def home():
    return redirect('/quiz') if 'user_id' in session else redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password_hash = generate_password_hash(request.form['password'])
        try:
            user = User(username=username, password=password_hash)
            db.session.add(user)
            db.session.commit()
            return redirect('/login')
        except:
            db.session.rollback()
            return "Username already exists. <a href='/register'>Try again</a>"
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
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

        rel_path = os.path.relpath(save_path, os.path.join('login_system', 'static')).replace("\\", "/")

        image = UserImage.query.filter_by(user_id=user_id, image_number=image_number).first()
        if image:
            image.image_path = rel_path
        else:
            image = UserImage(user_id=user_id, image_number=image_number, image_path=rel_path)
            db.session.add(image)
        db.session.commit()

        flash(f"Image for {image_number} uploaded.")
        return redirect(request.url)

    return render_template("upload_override.html")

@app.route('/course')
def course():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("course.html", username=get_username(session['user_id']))
