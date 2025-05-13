# app/main.py
from fastapi import FastAPI
from app.routes import word

app = FastAPI(
    title="BARTA-IMLI word of smth smth",
    description="An API that serves and stores the word of the day, week, month, and any date range.",
    version="1.0.0"
)

# Include routes
app.include_router(word.router)
