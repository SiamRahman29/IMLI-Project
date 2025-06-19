# Trending Bengali Words & Phrases Extraction System

This project is a full-stack system for extracting, analyzing, and visualizing trending Bengali words and phrases from news and social media sources. It leverages advanced NLP (Natural Language Processing) techniques, N-gram frequency analysis, and TF-IDF to provide accurate, date-wise trending insights. The system features a modern React frontend and a robust FastAPI backend.

## Features

- **Multi-source Scraping:** Collects data from Bengali news (RSS, NewsData.io) and social media (Selenium-based scraping).
- **Advanced Bengali NLP:** Cleans, tokenizes, and removes stop words from text; supports both single words and multi-word phrases.
- **Trending Analysis:** Uses N-gram frequency, TF-IDF, and a multi-factor scoring algorithm to detect trending words/phrases.
- **Date-wise Analysis:** Stores and displays trending data by date, allowing historical trend exploration.
- **Modern Frontend:** Responsive React UI with Bengali-friendly fonts, full-width layout, and user-friendly error handling.
- **API-first Design:** RESTful endpoints for all major features, with CORS enabled for easy frontend-backend integration.
- **Clear Documentation:** Mermaid diagrams and workflow explanations included for backend logic and data models.

## Quickstart: Running Locally

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```
3. **Start the backend server:**
   ```bash
   uvicorn app.main:app --reload
   ```
4. **Start the frontend (in `frontend/`):**
   ```bash
   npm install
   npm run dev
   ```

## Project Structure

- `app/` - FastAPI backend (routes, models, services, NLP, scraping)
- `frontend/` - React frontend (modern UI, API integration)
- `alembic/` - Database migrations
- `requirements.txt` - Python dependencies

## Example API Endpoints

- `POST /api/v2/generate_candidates` — Run trending analysis and get AI-generated trending words/phrases
- `POST /set_word_of_the_day?word=...` — Set the word/phrase of the day
- `GET /api/v2/trending-phrases` — Get trending phrases with filters (date, type, source)

## Troubleshooting & Error Handling

- **Social Media Scraping Disabled:**
  - By default, social media scraping is disabled for safety. To enable, set `ENABLE_SOCIAL_MEDIA_SCRAPING = True` in `app/services/social_media_scraper.py`.
  - If disabled, the backend and frontend will show info messages, not errors.

- **Groq API Key Required:**
  - Make sure you have a valid `GROQ_API_KEY` in your `.env` file for AI-powered trending word extraction.
  - To obtain a key, visit the [Groq API website](https://groq.com/) and follow their instructions for signing up and generating an API key.
  - If missing, the backend will return a clear error message.

- **News Scraping Issues:**
  - If a news site changes its structure, scraping may fail for that site. Check backend logs for details.
  - The system will still work if at least some scrapers succeed.

- **Frontend Error Messages:**
  - The frontend will now display backend error details if available, making debugging easier.

- **General Debugging:**
  - Check backend logs for `[ERROR]` or `[INFO]` messages.
  - If you see a 500 error, the backend will include a traceback in the error detail for easier diagnosis.

## Acknowledgements
- Bengali NLP: [NLTK](https://www.nltk.org/), [scikit-learn](https://scikit-learn.org/)
- Frontend: [React](https://react.dev/), [Material UI](https://mui.com/)
- Backend: [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/)


For any issues or contributions, please open an issue or pull request!

## TODO:
1. Turn word/phrase freq into graphs
2. Named entity recognition improvement
3. GraphAPI integration
4. Increase scope send to LLM
5. Change prompt to exclude named entities ✅
6. Frontend fixes ✅
7. Tailwind CSS implementation
8. Prompt engineer to implement TFIDF
9. Link sources
