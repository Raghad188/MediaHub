# MediaHub

MediaHub is a Flask + SQLite movie and music platform for discovering TMDB movies, searching Spotify tracks, saving favorites, building a watchlist, rating movies, commenting, and tracking recently viewed movies.

## Features

- User registration and login
- TMDB movie browsing, search, and details
- Spotify music search with graceful API failure handling
- Favorites and watchlist with duplicate prevention
- Movie ratings with average rating display
- Owner-only comments with timestamps
- Profile page with avatar fallback, statistics, and recently viewed movies
- Responsive dark UI
- CSRF protection on all POST forms

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a local `.env` file using `.env.example` as the template:

```bash
cp .env.example .env
```

4. Add your local values:

```env
SECRET_KEY=replace-with-a-long-random-secret
TMDB_API_KEY=replace-with-your-tmdb-api-key
SPOTIFY_CLIENT_ID=replace-with-your-spotify-client-id
SPOTIFY_CLIENT_SECRET=replace-with-your-spotify-client-secret
DATABASE_URL=sqlite:///database.db
```

5. Run the app:

```bash
flask --app app run
```

## Security Notes

- Never commit `.env`.
- Rotate any API key that was ever committed or shared.
- `debug=True` is not used.
- State-changing routes require login and CSRF-protected POST requests.
- For HTTPS deployments, set `SESSION_COOKIE_SECURE=true`.

## Deployment

Use a production WSGI server such as Gunicorn or uWSGI and provide environment variables through the hosting platform. SQLite is suitable for a small portfolio deployment; move to PostgreSQL if the project grows or needs concurrent write-heavy usage.
