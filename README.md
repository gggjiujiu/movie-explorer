# Movie Explorer Group Project

Movie Explorer is a web application for discovering movies and managing a personal favorites list. It uses data from the TMDB API to let users browse, search and filter movies, and view movie details. Registered users can save movies to their favorites list and manage their saved selections.

## Core Features

- **Movie discovery and search:** Browse popular movies, search by title, and filter results by genre, release year, and minimum rating.
- **Movie details:** View each movie’s synopsis, genres, release year, runtime and TMDB rating.
- **User authentication:** Register and sign in to access personal features. Guests can browse and search without an account.
- **Personal favorites:** Save movies to a personal favorites list and remove saved movies from either the movie details page or the favorites list.
- **Account management:** View account details, update an email address and change a password.
- **TMDB error handling:** Display a dedicated error page when movie data cannot be retrieved from TMDB.

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Templating:** Jinja2
- **Database:** PostgreSQL, SQLAlchemy
- **External API:** TMDB API
- **Testing and code quality:** pytest, flake8
- **CI/CD and deployment:** GitLab CI/CD, Tsuru

## Project Structure

- `app.py`: Creates and configures the Flask application and registers route blueprints.
- `db.py`: Configures the database connection and provides functions for managing user accounts and favorites.
- `tmdb.py`: Handles TMDB API requests and API error handling.
- `routes/`: Contains route handlers for authentication, movies, favorites and account management.
- `models/`: Defines SQLAlchemy models for users and favorites.
- `templates/`: Contains Jinja2 HTML templates.
- `static/`: Contains CSS stylesheets.
- `tests/`: Contains pytest tests for application features and TMDB error handling.
- `populate-db.sql`: Defines the database tables.
- `requirements.txt`: Lists Python dependencies.
- `.gitlab-ci.yml`: Configures the GitLab CI/CD pipeline for linting, testing and deployment.
- `Procfile`: Defines the command used to start the web application during deployment.

## Getting Started

### Prerequisites

- Python (the CI pipeline is configured to use Python 3.12)
- A running PostgreSQL server
- A TMDB API key

After cloning the repository, run the following commands from the project root directory.

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
python3 -m pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root directory and replace the placeholder values with your own settings:

```dotenv
TMDB_API_KEY=your_tmdb_api_key
FLASK_SECRET_KEY=your_secret_key

PGHOST=localhost
PGPORT=5432
PGDATABASE=your_database_name
PGUSER=your_postgres_user
PGPASSWORD=your_postgres_password
```

### Database Setup

Use the same connection settings as in your `.env` file. Replace `your_postgres_user` and `your_database_name` with your PostgreSQL username and database name.

Create a new database. Skip this command if the database already exists:

```bash
createdb -h localhost -p 5432 -U your_postgres_user your_database_name
```

Initialize the database tables using the provided SQL file:

```bash
psql -h localhost -p 5432 -U your_postgres_user -d your_database_name -f populate-db.sql
```

This creates the `users` and `favorite_movie_list` tables.

### Run the Application

```bash
python3 -m flask --app app:create_app run --port 8000
```

Open http://127.0.0.1:8000 in your browser.

### Run Tests

```bash
python3 -m pytest
```