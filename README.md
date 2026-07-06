# 🎬 MediaHub

A modern movie and music discovery platform built with **Flask** and **SQLite**. MediaHub integrates with **TMDB** and **Spotify APIs** to provide a personalized entertainment experience with secure authentication, watchlists, favorites, ratings, and user profiles.

---

## ✨ Features

- 🔐 Secure user authentication
- 🎬 Browse and search movies via TMDB
- 🎵 Search Spotify tracks
- ❤️ Favorites and Watchlist
- ⭐ Movie rating system
- 💬 Comment system
- 👤 Personalized user profiles
- 🕒 Recently viewed movies
- 🌙 Responsive dark interface
- 🛡️ CSRF protection
- 🚫 Duplicate prevention for favorites and watchlist

---

## 🛠️ Built With

| Technology | Purpose |
|------------|---------|
| Python | Backend |
| Flask | Web Framework |
| SQLite | Database |
| HTML5 | Frontend |
| CSS3 | Styling |
| TMDB API | Movie Data |
| Spotify API | Music Search |

---

## 🚀 Getting Started

### Clone the repository

```bash
git clone https://github.com/Raghad188/MediaHub.git
cd MediaHub
```

### Create a virtual environment

```bash
python -m venv .venv
```

macOS / Linux

```bash
source .venv/bin/activate
```

Windows

```bash
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file using `.env.example`.

```env
SECRET_KEY=your_secret_key
TMDB_API_KEY=your_tmdb_api_key
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
DATABASE_URL=sqlite:///database.db
```

### Run

```bash
flask --app app run
```

---

## 🔒 Security

- `.env` is excluded using `.gitignore`
- API keys are loaded from environment variables
- CSRF protection enabled
- Authentication required for protected actions
- Session security configuration included

---

## 📁 Project Structure

```
MediaHub/
├── static/
├── templates/
├── app.py
├── models.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 💡 Future Improvements

- 🎬 Personalized recommendations
- 🎵 Spotify playlists
- 🌙 More UI themes
- 📱 Progressive Web App (PWA)
- ☁️ PostgreSQL support

---

## 📄 License

This project was built for educational and portfolio purposes.