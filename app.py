import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
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
class UserImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    image_number = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String(300), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'image_number'),)

# --- Auto-create Tables on First Request ---
with app.app_context():
    db.create_all()

# --- Helpers ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_or_create_user_id(request, response=None):
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        if response:
            response.set_cookie('user_id', user_id, max_age=60*60*24*365*5)  # 5 years
    return user_id

def get_user_image(user_id, image_number):
    entry = UserImage.query.filter_by(user_id=user_id, image_number=image_number).first()
    if entry:
        return url_for('static', filename=entry.image_path)

    # Default fallback
    for ext in ('jpg', 'png'):
        path = f'images/{image_number}.{ext}'
        if os.path.exists(os.path.join('login_system', 'static', path)):
            return url_for('static', filename=path)

    return url_for('static', filename='images/placeholder.png')

# --- Routes ---
@app.route('/')
def home():
    response = make_response(redirect('/quiz'))
    get_or_create_user_id(request, response)
    return response

@app.route('/quiz')
def quiz():
    user_id = get_or_create_user_id(request)
    image_map = {i: get_user_image(user_id, i) for i in range(100)}
    return render_template("quiz.html", image_map=image_map, username=user_id)

@app.route('/upload_override', methods=['GET', 'POST'])
def upload_override():
    user_id = get_or_create_user_id(request)

    if request.method == 'POST':
        image_number = int(request.form['image_number'])
        file = request.files.get('image')

        if not file or not allowed_file(file.filename):
            flash("Invalid image file.")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"user_{user_id}")
        os.makedirs(user_folder, exist_ok=True)

        save_path = os.path.join(user_folder, f"{image_number}_{filename}")
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
    return render_template("course.html", username=get_or_create_user_id(request))

@app.route('/admin/delete_db_entry/<int:image_number>')
def delete_db_entry(image_number):
    user_id = get_or_create_user_id(request)
    entry = UserImage.query.filter_by(user_id=user_id, image_number=image_number).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
        return f"✅ Deleted DB record for image {image_number}"
    return f"⚠️ No DB entry found for image {image_number}"
