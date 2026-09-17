# AGENTS.md

## Quick start

```powershell
# Install dependencies (no manifest file exists; install manually):
pip install flask flask-sqlalchemy flask-migrate flask-login flask-wtf wtforms pymysql Pillow

# Run dev server:
python run.py
```

## Architecture

- **Flask app factory** in `app/__init__.py` → `create_app()`
- **3 blueprints**: `auth` (`/sign_in`), `books` (`/`), `borrow` (`/borrow`)
- **DB**: MySQL via pymysql (hardcoded in `config.py`, no SQLite fallback)
  - Default: `root:123456@localhost:3306/library`
  - Override via env vars: `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_PORT`
- **Entrypoint**: `run.py` (debug mode, development only — no WSGI/gunicorn entrypoint)
- **Secret key** in `.flaskenv` (loaded by python-dotenv)
- **Frontend**: Bootstrap 4.6, jQuery, Jinja2 templates in `app/templates/`

## Database

- Models: `User`, `Book`, `Category`, `Borrow` in `app/models.py`
- Migrations via Flask-Migrate: `flask db migrate` / `flask db upgrade`

## Routes

| Blueprint | Route | Description |
|-----------|-------|-------------|
| `books` | `/` | Home page (all books) |
| `books` | `/books` | Book list (paginated) |
| `books` | `/books/<id>` | Book detail + related books |
| `books` | `/books/manage` | Admin: book CRUD with search/filter/pagination |
| `books` | `/books/addbook` | Admin: add book |
| `books` | `/books/edit/<id>` | Admin: edit book |
| `books` | `/book/delete/<id>` | Admin: delete book |
| `books` | `/books/search` | Search books by title/author (paginated) |
| `auth` | `/sign_in` | Login / Register / Password reset |
| `auth` | `/logout` | Logout |
| `auth` | `/user/home` | User borrow history (paginated) |
| `borrow` | `/borrow/<id>` | Borrow a book |
| `borrow` | `/borrow/return/<id>` | Return a book (POST) |
| `borrow` | `/borrow/manage` | Admin: borrow management with overdue detection |

## Known issues

- **No `requirements.txt`** — install deps manually (see Quick start)
- **No `pyproject.toml`**, no linter/formatter/typechecker config
- **No test files** exist
- **No CI/CD** workflows
- **No `.env`** file — use `.flaskenv` for Flask env vars

## Conventions

- All docs and UI text are in **Chinese**
- Forms use Flask-WTF (`app/form.py`)
- Auth uses Flask-Login (session-based)
- No tests, linting, or typechecking — add before starting new work
