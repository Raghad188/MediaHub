import os
import re
from datetime import datetime
from functools import wraps

import bcrypt
import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from sqlalchemy import inspect, text

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError:
    spotipy = None
    SpotifyClientCredentials = None


if load_dotenv:
    load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(32)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///database.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
app.config["WTF_CSRF_TIME_LIMIT"] = 3600

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
DEFAULT_AVATAR = "https://ui-avatars.com/api/?name=MediaHub&background=2563eb&color=fff&size=200"
REQUEST_TIMEOUT = 8
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(300))
    avatar = db.Column(db.String(500), default=DEFAULT_AVATAR)
    bio = db.Column(db.String(300), default="Movie lover")


class Favorite(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_favorite_user_movie"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    image = db.Column(db.String(500))
    rating = db.Column(db.String(20))


class Watchlist(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_watchlist_user_movie"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    image = db.Column(db.String(500))
    rating = db.Column(db.String(20))


class Rating(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_rating_user_movie"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer)
    value = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FavoriteSong(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "spotify_url", name="uq_favorite_song_user_url"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    artist = db.Column(db.String(200))
    image = db.Column(db.String(500))
    spotify_url = db.Column(db.String(500))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(100))
    movie_id = db.Column(db.Integer)
    text = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RecentlyViewed(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_recent_user_movie"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    image = db.Column(db.String(500))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)


def remove_duplicate_rows(model, field_names):
    seen = set()
    for item in model.query.order_by(model.id.asc()).all():
        key = tuple(getattr(item, field_name) for field_name in field_names)
        if key in seen:
            db.session.delete(item)
        else:
            seen.add(key)
    db.session.commit()


def ensure_schema():
    db.create_all()
    inspector = inspect(db.engine)

    if "comment" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("comment")}
        if "created_at" not in columns:
            db.session.execute(text("ALTER TABLE comment ADD COLUMN created_at DATETIME"))

    if "recently_viewed" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("recently_viewed")}
        if "viewed_at" not in columns:
            db.session.execute(text("ALTER TABLE recently_viewed ADD COLUMN viewed_at DATETIME"))

    db.session.commit()
    remove_duplicate_rows(Favorite, ("user_id", "movie_id"))
    remove_duplicate_rows(Watchlist, ("user_id", "movie_id"))
    remove_duplicate_rows(Rating, ("user_id", "movie_id"))
    remove_duplicate_rows(FavoriteSong, ("user_id", "spotify_url"))
    remove_duplicate_rows(RecentlyViewed, ("user_id", "movie_id"))


with app.app_context():
    ensure_schema()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def validate_registration(username, email, password):
    if not username or not email or not password:
        return "All fields are required."
    if len(username) < 3 or len(username) > 40:
        return "Username must be between 3 and 40 characters."
    if not re.match(r"^[A-Za-z0-9_.-]+$", username):
        return "Username can only contain letters, numbers, dots, underscores, and hyphens."
    if not EMAIL_PATTERN.match(email):
        return "Please enter a valid email address."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


def tmdb_get(path, params=None):
    if not TMDB_API_KEY:
        return None, "TMDB API key is not configured."

    query = {"api_key": TMDB_API_KEY}
    if params:
        query.update(params)

    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/{path.lstrip('/')}",
            params=query,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException:
        return None, "Movie service is unavailable right now. Please try again later."
    except ValueError:
        return None, "Movie service returned an invalid response."


def get_movie_or_redirect(movie_id):
    movie, error = tmdb_get(f"movie/{movie_id}", {"append_to_response": "videos"})
    if error:
        flash(error, "error")
        return None
    return movie


def poster_url(path):
    if not path:
        return DEFAULT_AVATAR
    if path.startswith("http"):
        return path
    return f"{TMDB_IMAGE_BASE}{path}"


def spotify_client():
    if not spotipy or not SpotifyClientCredentials:
        return None, "Spotify library is not installed."
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None, "Spotify API credentials are not configured."

    try:
        return spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ),
            requests_timeout=REQUEST_TIMEOUT,
            retries=1
        ), None
    except Exception:
        return None, "Music service is unavailable right now. Please try again later."


def average_rating(movie_id):
    ratings = Rating.query.filter_by(movie_id=movie_id).all()
    if not ratings:
        return None
    return round(sum(rating.value for rating in ratings) / len(ratings), 1)


@app.context_processor
def inject_helpers():
    return {
        "current_user": current_user(),
        "poster_url": poster_url,
        "default_avatar": DEFAULT_AVATAR,
    }


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    flash("Your form expired. Please try again.", "error")
    return redirect(request.referrer or url_for("home"))


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        validation_error = validate_registration(username, email, password)
        if validation_error:
            flash(validation_error, "error")
            return render_template("register.html")

        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash("Username or email already exists.", "error")
            return render_template("register.html")

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = User(username=username, email=email, password=hashed.decode("utf-8"))
        db.session.add(user)
        db.session.commit()
        session.clear()
        session["user_id"] = user.id
        flash("Account created successfully.", "success")
        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            session.clear()
            session["user_id"] = user.id
            flash("Welcome back.", "success")
            return redirect(url_for("home"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/movies")
def movies():
    search = request.args.get("search", "").strip()
    if search:
        data, error = tmdb_get("search/movie", {"query": search})
        title = f"Search results for {search}"
    else:
        data, error = tmdb_get("movie/popular")
        title = "Popular Movies"

    movies_data = []
    if error:
        flash(error, "error")
    else:
        movies_data = data.get("results", [])

    return render_template("movies.html", movies=movies_data, search=search, title=title)


@app.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = get_movie_or_redirect(movie_id)
    if not movie:
        return redirect(url_for("movies"))

    comments = Comment.query.filter_by(movie_id=movie_id).order_by(Comment.id.desc()).all()
    user_rating = None
    if "user_id" in session:
        user_rating = Rating.query.filter_by(
            user_id=session["user_id"],
            movie_id=movie_id
        ).first()

        existing = RecentlyViewed.query.filter_by(
            user_id=session["user_id"],
            movie_id=movie_id
        ).first()
        if existing:
            existing.viewed_at = datetime.utcnow()
        else:
            recent = RecentlyViewed(
                user_id=session["user_id"],
                movie_id=movie_id,
                title=movie.get("title", "Untitled"),
                image=movie.get("poster_path")
            )
            db.session.add(recent)
        db.session.commit()

    return render_template(
        "movie_details.html",
        movie=movie,
        comments=comments,
        user_rating=user_rating,
        average_rating=average_rating(movie_id)
    )


@app.route("/add_favorite/<int:movie_id>", methods=["POST"])
@login_required
def add_favorite(movie_id):
    movie = get_movie_or_redirect(movie_id)
    if not movie:
        return redirect(url_for("movies"))

    existing = Favorite.query.filter_by(
        user_id=session["user_id"],
        movie_id=movie_id
    ).first()

    if existing:
        flash("Movie is already in your favorites.", "error")
    else:
        favorite = Favorite(
            user_id=session["user_id"],
            movie_id=movie_id,
            title=movie.get("title", "Untitled"),
            image=movie.get("poster_path"),
            rating=str(movie.get("vote_average", "N/A"))
        )
        db.session.add(favorite)
        db.session.commit()
        flash("Movie added to favorites.", "success")

    return redirect(request.referrer or url_for("favorites"))


@app.route("/favorites")
@login_required
def favorites():
    favorites_list = Favorite.query.filter_by(user_id=session["user_id"]).all()
    songs = FavoriteSong.query.filter_by(user_id=session["user_id"]).all()
    return render_template(
        "favorites.html",
        favorites=favorites_list,
        songs=songs,
        favorite_count=len(favorites_list),
        song_count=len(songs)
    )


@app.route("/delete_favorite/<int:favorite_id>", methods=["POST"])
@login_required
def delete_favorite(favorite_id):
    favorite = Favorite.query.filter_by(
        id=favorite_id,
        user_id=session["user_id"]
    ).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash("Favorite removed.", "success")
    else:
        flash("Favorite not found.", "error")

    return redirect(url_for("favorites"))


@app.route("/add_watchlist/<int:movie_id>", methods=["POST"])
@login_required
def add_watchlist(movie_id):
    movie = get_movie_or_redirect(movie_id)
    if not movie:
        return redirect(url_for("movies"))

    existing = Watchlist.query.filter_by(
        user_id=session["user_id"],
        movie_id=movie_id
    ).first()

    if existing:
        flash("Movie is already in your watchlist.", "error")
    else:
        watch = Watchlist(
            user_id=session["user_id"],
            movie_id=movie_id,
            title=movie.get("title", "Untitled"),
            image=movie.get("poster_path"),
            rating=str(movie.get("vote_average", "N/A"))
        )
        db.session.add(watch)
        db.session.commit()
        flash("Movie added to watchlist.", "success")

    return redirect(request.referrer or url_for("watchlist_page"))


@app.route("/delete_watchlist/<int:watchlist_id>", methods=["POST"])
@login_required
def delete_watchlist(watchlist_id):
    watch = Watchlist.query.filter_by(
        id=watchlist_id,
        user_id=session["user_id"]
    ).first()

    if watch:
        db.session.delete(watch)
        db.session.commit()
        flash("Watchlist item removed.", "success")
    else:
        flash("Watchlist item not found.", "error")

    return redirect(url_for("watchlist_page"))


@app.route("/watchlist")
@login_required
def watchlist_page():
    watchlist = Watchlist.query.filter_by(user_id=session["user_id"]).all()
    return render_template(
        "watchlist.html",
        watchlist=watchlist,
        watchlist_count=len(watchlist)
    )


@app.route("/music")
def music():
    search = request.args.get("search", "").strip()
    query = search or "top hits"
    tracks = []
    error = None
    client, client_error = spotify_client()

    if client_error:
        error = client_error
    else:
        try:
            results = client.search(q=query, type="track", limit=12)
            tracks = results.get("tracks", {}).get("items", [])
        except Exception:
            error = "Music service is unavailable right now. Please try again later."

    if error:
        flash(error, "error")

    return render_template("music.html", tracks=tracks, search=search)


@app.route("/add_song/<track_id>", methods=["POST"])
@app.route("/add-song/<track_id>", methods=["POST"])
@login_required
def add_song(track_id):
    client, error = spotify_client()
    if error:
        flash(error, "error")
        return redirect(url_for("music"))

    try:
        track = client.track(track_id)
    except Exception:
        flash("Could not add this song right now.", "error")
        return redirect(url_for("music"))

    existing = FavoriteSong.query.filter_by(
        user_id=session["user_id"],
        spotify_url=track.get("external_urls", {}).get("spotify")
    ).first()

    if existing:
        flash("Song is already in your favorites.", "error")
    else:
        images = track.get("album", {}).get("images", [])
        artists = track.get("artists", [])
        song = FavoriteSong(
            user_id=session["user_id"],
            title=track.get("name", "Unknown song"),
            artist=artists[0]["name"] if artists else "Unknown artist",
            image=images[0]["url"] if images else DEFAULT_AVATAR,
            spotify_url=track.get("external_urls", {}).get("spotify", "#")
        )
        db.session.add(song)
        db.session.commit()
        flash("Song added to favorites.", "success")

    return redirect(url_for("favorites"))


@app.route("/delete_song/<int:song_id>", methods=["POST"])
@login_required
def delete_song(song_id):
    song = FavoriteSong.query.filter_by(id=song_id, user_id=session["user_id"]).first()
    if song:
        db.session.delete(song)
        db.session.commit()
        flash("Song removed.", "success")
    else:
        flash("Song not found.", "error")

    return redirect(url_for("favorites"))


@app.route("/comment/<int:movie_id>", methods=["POST"])
@login_required
def comment(movie_id):
    user = current_user()
    text_value = request.form.get("text", "").strip()

    if not text_value:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("movie_details", movie_id=movie_id))
    if len(text_value) > 500:
        flash("Comment must be 500 characters or fewer.", "error")
        return redirect(url_for("movie_details", movie_id=movie_id))
    duplicate = Comment.query.filter_by(
        user_id=user.id,
        movie_id=movie_id,
        text=text_value
    ).first()
    if duplicate:
        flash("You already posted that comment.", "error")
        return redirect(url_for("movie_details", movie_id=movie_id))

    new_comment = Comment(
        user_id=user.id,
        username=user.username,
        movie_id=movie_id,
        text=text_value,
        created_at=datetime.utcnow()
    )
    db.session.add(new_comment)
    db.session.commit()
    flash("Comment posted.", "success")
    return redirect(url_for("movie_details", movie_id=movie_id))


@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment_item = Comment.query.get(comment_id)
    if not comment_item:
        flash("Comment not found.", "error")
        return redirect(request.referrer or url_for("movies"))

    movie_id = comment_item.movie_id
    if comment_item.user_id != session["user_id"]:
        flash("You can only delete your own comments.", "error")
        return redirect(url_for("movie_details", movie_id=movie_id))

    db.session.delete(comment_item)
    db.session.commit()
    flash("Comment deleted.", "success")
    return redirect(url_for("movie_details", movie_id=movie_id))


@app.route("/rate_movie/<int:movie_id>", methods=["POST"])
@login_required
def rate_movie(movie_id):
    try:
        value = int(request.form.get("rating", "0"))
    except ValueError:
        value = 0

    if value < 1 or value > 10:
        flash("Rating must be between 1 and 10.", "error")
        return redirect(request.referrer or url_for("movie_details", movie_id=movie_id))

    rating = Rating.query.filter_by(
        user_id=session["user_id"],
        movie_id=movie_id
    ).first()

    if rating:
        rating.value = value
        rating.created_at = datetime.utcnow()
        flash("Rating updated.", "success")
    else:
        rating = Rating(user_id=session["user_id"], movie_id=movie_id, value=value)
        db.session.add(rating)
        flash("Rating saved.", "success")

    db.session.commit()
    return redirect(request.referrer or url_for("movie_details", movie_id=movie_id))


@app.route("/profile")
@login_required
def profile():
    user = current_user()
    recent = RecentlyViewed.query.filter_by(user_id=user.id).order_by(
        RecentlyViewed.viewed_at.desc(),
        RecentlyViewed.id.desc()
    ).limit(12).all()

    stats = {
        "ratings": Rating.query.filter_by(user_id=user.id).count(),
        "favorites": Favorite.query.filter_by(user_id=user.id).count(),
        "watchlist": Watchlist.query.filter_by(user_id=user.id).count(),
        "comments": Comment.query.filter_by(user_id=user.id).count(),
    }

    return render_template("profile.html", user=user, recent=recent, stats=stats)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
