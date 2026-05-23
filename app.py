from flask import Flask, render_template, request, redirect, session

from flask_sqlalchemy import SQLAlchemy

import requests

import bcrypt

import spotipy

from spotipy.oauth2 import SpotifyClientCredentials


# =========================================================
# APP CONFIG
# =========================================================

app = Flask(__name__)

app.secret_key = "mediahub_secret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)


# =========================================================
# APIs
# =========================================================

TMDB_API_KEY = "8de0a0ea1a24e82f42932cd4b45f6ae5"

SPOTIFY_CLIENT_ID = "7666206bc9c6415193ec32813b5698f9"

SPOTIFY_CLIENT_SECRET = "b62724be99c54773ac83cba3c2d21147"


sp = spotipy.Spotify(

    auth_manager=SpotifyClientCredentials(

        client_id=SPOTIFY_CLIENT_ID,

        client_secret=SPOTIFY_CLIENT_SECRET

    )

)


# =========================================================
# DATABASE MODELS
# =========================================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100))

    email = db.Column(
        db.String(100),
        unique=True
    )

    password = db.Column(db.String(300))

    avatar = db.Column(
        db.String(500),
        default="https://i.imgur.com/HeIi0wU.png"
    )

    bio = db.Column(
        db.String(300),
        default="Movie lover 🎬"
    )


class Favorite(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    movie_id = db.Column(db.Integer)

    title = db.Column(db.String(200))

    image = db.Column(db.String(500))

    rating = db.Column(db.String(20))


class Watchlist(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    movie_id = db.Column(db.Integer)

    title = db.Column(db.String(200))

    image = db.Column(db.String(500))

    rating = db.Column(db.String(20))


class FavoriteSong(db.Model):

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


class RecentlyViewed(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    movie_id = db.Column(db.Integer)

    title = db.Column(db.String(200))

    image = db.Column(db.String(500))


# =========================================================
# CREATE DATABASE
# =========================================================

with app.app_context():

    db.create_all()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("home.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        email = request.form["email"]

        password = request.form["password"]

        hashed = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        )

        user = User(

            username=username,

            email=email,

            password=hashed.decode("utf-8")

        )

        db.session.add(user)

        db.session.commit()

        session["user_id"] = user.id

        return redirect("/")

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user:

            if bcrypt.checkpw(
                password.encode("utf-8"),
                user.password.encode("utf-8")
            ):

                session["user_id"] = user.id

                return redirect("/")

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================================
# MOVIES PAGE
# =========================================================

@app.route("/movies")
def movies():

    search = request.args.get("search")

    if search:

        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={search}"

    else:

        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}"

    response = requests.get(url)

    data = response.json()

    movies = data["results"]

    return render_template(
        "movies.html",
        movies=movies
    )


# =========================================================
# MOVIE DETAILS
# =========================================================

@app.route("/movie/<int:id>")
def movie_details(id):

    url = f"https://api.themoviedb.org/3/movie/{id}?api_key={TMDB_API_KEY}&append_to_response=videos"

    response = requests.get(url)

    movie = response.json()

    comments = Comment.query.filter_by(
        movie_id=id
    ).all()

    if "user_id" in session:

        existing = RecentlyViewed.query.filter_by(
            user_id=session["user_id"],
            movie_id=id
        ).first()

        if not existing:

            recent = RecentlyViewed(

                user_id=session["user_id"],

                movie_id=id,

                title=movie["title"],

                image=movie["poster_path"]

            )

            db.session.add(recent)

            db.session.commit()

    return render_template(
        "movie_details.html",
        movie=movie,
        comments=comments
    )


# =========================================================
# FAVORITES
# =========================================================

@app.route("/add_favorite/<int:id>")
def add_favorite(id):

    if "user_id" not in session:
        return redirect("/login")

    url = f"https://api.themoviedb.org/3/movie/{id}?api_key={TMDB_API_KEY}"

    response = requests.get(url)

    movie = response.json()

    existing = Favorite.query.filter_by(
        user_id=session["user_id"],
        movie_id=id
    ).first()

    if not existing:

        favorite = Favorite(

            user_id=session["user_id"],

            movie_id=id,

            title=movie["title"],

            image=movie["poster_path"],

            rating=str(movie["vote_average"])

        )

        db.session.add(favorite)

        db.session.commit()

    return redirect("/favorites")


@app.route("/favorites")
def favorites():

    if "user_id" not in session:
        return redirect("/login")

    favorites = Favorite.query.filter_by(
        user_id=session["user_id"]
    ).all()

    songs = FavoriteSong.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "favorites.html",
        favorites=favorites,
        songs=songs
    )


@app.route("/delete_favorite/<int:id>")
def delete_favorite(id):

    favorite = Favorite.query.get(id)

    db.session.delete(favorite)

    db.session.commit()

    return redirect("/favorites")


# =========================================================
# WATCHLIST
# =========================================================

@app.route("/add_watchlist/<int:id>")
def add_watchlist(id):

    if "user_id" not in session:
        return redirect("/login")

    url = f"https://api.themoviedb.org/3/movie/{id}?api_key={TMDB_API_KEY}"

    response = requests.get(url)

    movie = response.json()

    existing = Watchlist.query.filter_by(
        user_id=session["user_id"],
        movie_id=id
    ).first()

    if not existing:

        watch = Watchlist(

            user_id=session["user_id"],

            movie_id=id,

            title=movie["title"],

            image=movie["poster_path"],

            rating=str(movie["vote_average"])

        )

        db.session.add(watch)

        db.session.commit()

    return redirect("/watchlist")

# =========================================================
# DELETE WATCHLIST
# =========================================================

@app.route("/delete_watchlist/<int:id>")
def delete_watchlist(id):

    watch = Watchlist.query.get(id)

    db.session.delete(watch)

    db.session.commit()

    return redirect("/watchlist")


@app.route("/watchlist")
def watchlist_page():

    if "user_id" not in session:
        return redirect("/login")

    watchlist = Watchlist.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "watchlist.html",
        watchlist=watchlist
    )

# =========================================================
# MUSIC
# =========================================================

@app.route("/music", methods=["GET", "POST"])
def music():

    search = request.form.get("search")

    if search:

        results = sp.search(
            q=search,
            type="track",
            limit=12
        )

    else:

        results = sp.search(
            q="top hits",
            type="track",
            limit=12
        )

    tracks = results["tracks"]["items"]

    return render_template(
        "music.html",
        tracks=tracks
    )


@app.route("/add_song/<track_id>")
def add_song(track_id):

    if "user_id" not in session:
        return redirect("/login")

    track = sp.track(track_id)

    existing = FavoriteSong.query.filter_by(
        user_id=session["user_id"],
        title=track["name"]
    ).first()

    if not existing:

        song = FavoriteSong(

            user_id=session["user_id"],

            title=track["name"],

            artist=track["artists"][0]["name"],

            image=track["album"]["images"][0]["url"],

            spotify_url=track["external_urls"]["spotify"]

        )

        db.session.add(song)

        db.session.commit()

    return redirect("/favorites")


@app.route("/delete_song/<int:id>")
def delete_song(id):

    song = FavoriteSong.query.get(id)

    db.session.delete(song)

    db.session.commit()

    return redirect("/favorites")


# =========================================================
# COMMENTS
# =========================================================

@app.route("/comment/<int:id>", methods=["POST"])
def comment(id):

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    text = request.form["text"]

    new_comment = Comment(

        user_id=user.id,

        username=user.username,

        movie_id=id,

        text=text

    )

    db.session.add(new_comment)

    db.session.commit()

    return redirect(f"/movie/{id}")


@app.route("/delete_comment/<int:id>")
def delete_comment(id):

    comment = Comment.query.get(id)

    db.session.delete(comment)

    db.session.commit()

    return redirect(request.referrer)


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    recent = RecentlyViewed.query.filter_by(
        user_id=user.id
    ).all()

    return render_template(
        "profile.html",
        user=user,
        recent=recent
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5050,ß
    )