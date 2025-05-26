# Trending Words

This is a backend Python service that stores and serves trending Bengali words based on news and social media data. It uses the FastAPI framework to implement a simple REST API service.

Instructions for running locally

1. Install requirements.txt
   `pip install -r requirements.txt`
2. Run migrations for the db
   `alembic upgrade head`
3. Run a uvicorn server
   `uvicorn app.main:app --reload`