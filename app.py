from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_login import LoginManager
from werkzeug.utils import secure_filename
import os
from models import db, User, Post, Like, Comment

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///social_media.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "social-media-secret-key"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("home.html", posts=posts)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/create-post", methods=["GET", "POST"])
def create_post():
    if request.method == "POST":
        content = request.form["content"]
        tags = request.form.get("tags")
        image = request.files.get("image")
        image_filename = None

        if image and image.filename:
            image_filename = secure_filename(image.filename)
        if image_filename:
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))
        user = User.query.first()

        if not user:
            return "Please register an account first."

        new_post = Post(
            content=content,
            image=image_filename,
            tags=tags,
            user_id=user.id
        )

        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("create_post.html")

@app.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    user = User.query.first()

    if not user:
        return redirect(url_for("login"))

    existing_like = Like.query.filter_by(
        user_id=user.id,
        post_id=post.id
    ).first()

    if not existing_like:
        new_like = Like(
            user_id=user.id,
            post_id=post.id
        )

        db.session.add(new_like)
        db.session.commit()

    return redirect(url_for("home"))
@app.route("/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    db.session.delete(post)
    db.session.commit()

    return redirect(url_for("home"))

@app.route("/comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)

    user = User.query.first()

    if not user:
        return redirect(url_for("login"))

    content = request.form["content"]

    new_comment = Comment(
        content=content,
        user_id=user.id,
        post_id=post.id
    )

    db.session.add(new_comment)
    db.session.commit()

    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            return "Username or email already exists."

        new_user = User(
            username=username,
            email=email,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            return redirect(url_for("home"))

        return "Invalid email or password."

    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)