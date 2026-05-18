from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ---------------- USERS ---------------- #

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(300),
        nullable=False
    )

    avatar = db.Column(
        db.String(500),
        default="https://i.imgur.com/HeIi0wU.png"
    )

    bio = db.Column(
        db.String(500),
        default="Movie lover 🎬"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ---------------- FAVORITE MOVIES ---------------- #

class Favorite(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    movie_id = db.Column(
        db.Integer,
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    poster = db.Column(
        db.String(500)
    )

    rating = db.Column(
        db.Float
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


# ---------------- WATCHLIST ---------------- #

class Watchlist(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    movie_id = db.Column(
        db.Integer
    )

    title = db.Column(
        db.String(200)
    )

    poster = db.Column(
        db.String(500)
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


# ---------------- RATINGS ---------------- #

class Rating(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    movie_id = db.Column(
        db.Integer
    )

    value = db.Column(
        db.Integer
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


# ---------------- COMMENTS ---------------- #

class Comment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    movie_id = db.Column(
        db.Integer
    )

    username = db.Column(
        db.String(100)
    )

    text = db.Column(
        db.String(1000)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ---------------- RECENTLY VIEWED ---------------- #

class RecentlyViewed(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    movie_id = db.Column(
        db.Integer
    )

    title = db.Column(
        db.String(200)
    )

    poster = db.Column(
        db.String(500)
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    viewed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ---------------- FAVORITE SONGS ---------------- #

class FavoriteSong(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200)
    )

    artist = db.Column(
        db.String(200)
    )

    image = db.Column(
        db.String(500)
    )

    spotify_url = db.Column(
        db.String(500)
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )