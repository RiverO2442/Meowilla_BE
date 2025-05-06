from config import db
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from datetime import datetime

bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    # google_id = db.Column(db.String(256), unique=True, nullable=True)  # Google OAuth ID

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        if self.password_hash:
            return bcrypt.check_password_hash(self.password_hash, password)
        return False  # Password check fails for Google OAuth users

    def generate_token(self):
        return create_access_token(identity=str(self.id))

    def to_json(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            # "google_id": self.google_id
        }

class RecentSearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    search_query = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "search_query", name="unique_user_search"),
    )

    def to_json(self):
        return {
            "id": self.id,
            "query": self.search_query,
            "timestamp": self.timestamp
        }


