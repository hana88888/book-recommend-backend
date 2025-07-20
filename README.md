# Book Recommendation API

FastAPI server for book recommendations with Supabase integration.

## Features
- POST /swipe - Record user book preferences with author information
- GET /recommendations/{user_id} - Get personalized book recommendations using Rakuten Books API

## Setup
1. Copy `.env.example` to `.env` and fill in your credentials
2. Run SQL files in Supabase to set up database schema and policies
3. Install dependencies: `poetry install`
4. Run server: `poetry run fastapi dev app/main.py`

## API Endpoints
- `POST /swipe` - Record a book swipe with user_id, book_isbn, liked, and author
- `GET /recommendations/{user_id}` - Get book recommendations based on user preferences
