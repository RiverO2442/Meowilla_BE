from flask import request, jsonify, redirect, url_for, session
from config import app, db
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from authlib.integrations.flask_client import OAuth
from models import User, RecentSearch
from OpenverseAPIClient import OpenverseClient

from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default_secret_key")
app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")
app.config["REDIRECT_URI"] = "http://localhost:5000/auth/callback"

jwt = JWTManager(app)
ov_client = OpenverseClient()

oauth = OAuth(app)
oauth.register(
    "google",
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={"scope": "openid email profile"},
)

# -------------------- USER REGISTRATION --------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400

    if User.query.filter_by(username=username).first():
            return jsonify({"message": "Username already exists"}), 400

    new_user = User(username=username, email=email)
    new_user.set_password(password)
    print("Generated Hash:", new_user.password_hash)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# -------------------- GOOGLE LOGIN --------------------
@app.route("/auth/login")
def google_login():
    return oauth.google.authorize_redirect(app.config["REDIRECT_URI"])

@app.route("/auth/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token)

    if not user_info:
        return jsonify({"message": "Google login failed"}), 401

    user = User.query.filter_by(email=user_info["email"]).first()
    if not user:
        user = User(username=user_info["name"], email=user_info["email"])
        db.session.add(user)
        db.session.commit()

    access_token = user.generate_token()
    return jsonify({"token": access_token, "user": user.to_json()}), 200

# -------------------- USER LOGIN --------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    print("Login attempt:", email, password)
    user = User.query.filter_by(email=email).first()
    if not user:
        print("User not found")
        return jsonify({"message": "Invalid credentials"}), 401
    if not user or not user.check_password(password):
        print("Invalid password or user")
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = user.generate_token()
    return jsonify({"token": access_token, "user": user.to_json()}), 200

    

# -------------------- RECENT SEARCHES --------------------

@app.route("/recent_searches", methods=["POST"])
@jwt_required()
def save_search():
    data = request.json
    query = data.get("query")
    user_id = get_jwt_identity()

    if not query:
        return jsonify({"message": "Search query is required"}), 400

    existing = RecentSearch.query.filter_by(user_id=user_id, search_query=query).first()

    if existing:
        return jsonify({"message": "Search saved"}), 201
    else:
        existing = RecentSearch(user_id=user_id, search_query=query)
        db.session.add(existing)

    db.session.commit()

    return jsonify({"message": "Search saved"}), 201



@app.route("/recent_searches", methods=["GET"])
@jwt_required()
def get_recent_searches():
    user_id = get_jwt_identity()
    searches = (
        RecentSearch.query
        .filter_by(user_id=user_id)
        .order_by(RecentSearch.timestamp.desc())
        .all()
    )

    return jsonify({"searches": [s.to_json() for s in searches]}), 200


@app.route("/recent_searches/<int:search_id>", methods=["DELETE"])
@jwt_required()
def delete_search(search_id):
    user_id = get_jwt_identity()
    search = RecentSearch.query.filter_by(id=search_id, user_id=user_id).first()

    if not search:
        return jsonify({"message": "Search not found"}), 404

    db.session.delete(search)
    db.session.commit()

    return jsonify({"message": "Search deleted"}), 200


@app.route("/images", methods=["GET"])
def search_images():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    
    tags = request.args.get("tags")
    if tags:
        tags = tags.split(",")
    
    results = ov_client.search_images(
        query=query,
        page=page,
        page_size=page_size,
        tags=tags
    )
    
    return jsonify(results)

@app.route("/images/<id>", methods=["GET"])
def get_images(id):
    if not id:
        return jsonify({"error": "Id is required"}), 400
    
    results = ov_client.get_image_detail(
        id=id
    )
    
    return jsonify(results)

@app.route("/audios", methods=["GET"])
def audios():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    
    tags = request.args.get("tags")
    if tags:
        tags = tags.split(",")
    
    results = ov_client.search_audio(
        query=query,
        page=page,
        page_size=page_size,
        tags=tags
    )
    
    return jsonify(results)

@app.route("/audio/<id>", methods=["GET"])
def get_audio(id):
    if not id:
        return jsonify({"error": "Id is required"}), 400
    
    results = ov_client.get_audio_detail(
        id=id
    )
    
    return jsonify(results)

if __name__ == "__main__":
    from models import User, RecentSearch
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
