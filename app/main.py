# app/main.py
from fastapi import FastAPI
from app.routes import routes
from app.routes import routes_new
from fastapi.middleware.cors import CORSMiddleware
import os



app = FastAPI(
    title="BARTA-IMLI trending words API",
    description="An API that serves and stores trending Bengali words and phrases from news and social media with N-gram TF-IDF analysis.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Print the GROQ_API_KEY value at startup for debugging when running the server
print('GROQ_API_KEY:', os.environ.get('GROQ_API_KEY'))

# Include routes
app.include_router(routes.router, tags=["Legacy"])
app.include_router(routes_new.router, prefix="/api/v2", tags=["Trending Analysis V2"])
