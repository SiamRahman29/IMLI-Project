# app/main.py
from fastapi import FastAPI
from app.routes import routes
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(
    title="BARTA-IMLI trending words API",
    description="An API that serves and stores trending word of the day, week, month, and any date range.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or limit to ["http://localhost:8000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router)
