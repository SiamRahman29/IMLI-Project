# app/main.py
from fastapi import FastAPI
from app.routes import routes
from app.routes import routes_new
from app.routes import auth_routes
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import warnings

# Suppress PRAW async warnings globally
warnings.filterwarnings("ignore", message=".*PRAW.*asynchronous.*")
warnings.filterwarnings("ignore", message=".*using PRAW in an asynchronous environment.*")

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="BARTA-IML trending words analyzer",
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

# Print API keys at startup for debugging
print('GROQ_API_KEY (Default):', os.environ.get('GROQ_API_KEY'))
print('GROQ_API_KEY_NEWSPAPER:', os.environ.get('GROQ_API_KEY_NEWSPAPER'))
print('GROQ_API_KEY_REDDIT:', os.environ.get('GROQ_API_KEY_REDDIT'))
print('GROQ_API_KEY_COMBINE:', os.environ.get('GROQ_API_KEY_COMBINE'))
print('FACEBOOK_GRAPH_API_KEY:', os.environ.get('FACEBOOK_GRAPH_API_KEY'))
print('SERPAPI_API_KEY:', os.environ.get('SERPAPI_API_KEY'))
print('Email:', os.environ.get('MAIL_FROM'))

# Include routes
app.include_router(routes.router, tags=["Legacy"])
app.include_router(routes_new.router, prefix="/api/v2", tags=["Trending Analysis V2"])
app.include_router(auth_routes.router, prefix="/api/v2", tags=["Authentication"])
