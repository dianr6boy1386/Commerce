# Commerce — CS50W Project 2

**Dyan Ahmadi**

An eBay-style auction marketplace built with **Django**. Users can list items, place bids, comment on listings, browse by category, and maintain a personal watchlist.

Part of [CS50's Web Programming with Python and JavaScript](https://cs50.harvard.edu/web/).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Video demo

[Watch the project demo on YouTube](https://youtu.be/pMtTVFXoCgA)

## Features

- **Authentication** — register, log in, and log out with a custom `User` model.
- **Active listings** — home page shows open auctions with price, category, optional image, and **bid count**.
- **Create listing** — authenticated users publish auctions with starting bid, optional image URL, and category.
- **Listing detail** — bids, comments, watchlist, close auction, winner / no-winner messaging.
- **Bidding rules** — the first bid must be at least the starting bid; later bids must beat the current highest bid; sellers cannot bid on their own listings.
- **Watchlist** — add or remove listings; dedicated watchlist page.
- **Categories** — browse categories and filter active listings (seeded via migration).
- **Delete listing** — owners can remove their listings (with a confirmation prompt).
- **Django admin** — full CRUD for users, listings, bids, comments, categories, watchlist.
- **Production-ready defaults** — environment-based settings, WhiteNoise static files, optional PostgreSQL, Gunicorn `Procfile`.

## Tech stack

- Python 3.11+
- Django 5.x
- SQLite (development) or PostgreSQL via `DATABASE_URL`
- WhiteNoise + Gunicorn for deployment
- Custom CSS

## Project structure

```
commerce/
├── manage.py
├── requirements.txt
├── .env.example          # Copy to .env for local config
├── Procfile              # Gunicorn entrypoint (Railway, Render, Heroku-style hosts)
├── commerce/
│   ├── settings.py       # Env-driven configuration
│   ├── env.py
│   └── urls.py
├── auctions/
│   ├── models.py
│   ├── views.py
│   ├── querysets.py      # Shared queryset annotations (bid counts)
│   ├── forms.py
│   ├── tests.py
│   └── templates/ …
```

## Getting started

```bash
git clone https://github.com/dianr6boy1386/commerce.git
cd CS50_Web_commerce

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env    # Windows — or: cp .env.example .env

python manage.py migrate
python manage.py runserver
```

Open [Localhost](http://127.0.0.1:8000/).

### Environment variables

| Variable | Description |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required in production (`DJANGO_DEBUG=False`). |
| `DJANGO_DEBUG` | `True` for local dev (default when unset in `.env.example`). |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames. |
| `DATABASE_URL` | Optional PostgreSQL URL; omit to use SQLite. |
| `CSRF_TRUSTED_ORIGINS` | Required in production if using HTTPS on a custom domain. |
| `DJANGO_SECURE_SSL_REDIRECT` | Defaults to `True` when `DEBUG=False`. |

### Django admin

```bash
python manage.py createsuperuser
```

Visit [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

## Routes

| URL | Description |
| --- | --- |
| `/` | Active listings |
| `/login` | Log in |
| `/logout` | Log out |
| `/register` | Create an account |
| `/create` | Create a listing (login required) |
| `/listing/<id>` | Listing detail |
| `/listing/<id>/bid` | Place a bid (POST) |
| `/listing/<id>/close` | Close auction (POST, owner) |
| `/listing/<id>/delete` | Delete listing (POST, owner) |
| `/listing/<id>/comment` | Add comment (POST) |
| `/listing/<id>/watchlist` | Toggle watchlist (POST) |
| `/watchlist` | Your watchlist |
| `/categories` | All categories |
| `/categories/<id>` | Active listings in a category |

## Testing

Run from the project root (the folder containing `manage.py`):

```bash
python manage.py test
```

## Production deployment

1. Set `DJANGO_DEBUG=False` and a strong `DJANGO_SECRET_KEY`.
2. Set `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your domain(s).
3. Point `DATABASE_URL` at PostgreSQL (recommended for production).
4. Collect static files:

   ```bash
   python manage.py collectstatic --noinput
   ```

5. Run migrations and start Gunicorn (see `Procfile`):

   ```bash
   python manage.py migrate
   gunicorn commerce.wsgi --bind 0.0.0.0:8000
   ```

Platforms such as Render or Railway can use the `Procfile` and install from `requirements.txt`.

## License

This project is licensed under the [MIT License](LICENSE).

## Author

**Dyan Ahmadi** — CS50 Web Programming (Commerce)
