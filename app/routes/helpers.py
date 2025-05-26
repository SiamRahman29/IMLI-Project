import os
import requests
from dotenv import load_dotenv

from groq import Groq
from app.models.word import Article


load_dotenv()

def get_trending_words(db):
    """
    Fetches news articles from the specified API, parses them, and generates the trending word using the Groq API.
    """
    # Fetch news articles
    articles = fetch_news()

    # Fetch social media posts
    posts = fetch_social_media_posts()

    # Parse the articles to get a combined text
    combined_text = parse_news(articles)

    # Store the articles in the database
    store_news(db, articles)

    # Generate trending words using the Groq API
    trending_words = generate_trending_word(combined_text)

    return trending_words

def fetch_news():
    """
    Fetches news articles from the specified API and returns a dictionary of titles and descriptions.
    """
    # Fetching the news API URL from environment variables
    # Ensure you have a .env file with NEWS_API_URL set
    # Example: NEWS_API_URL=https://newsapi.org/v2/top-headlines?country=us&apiKey=your_api_key

    news_api_url = os.getenv("NEWS_API_URL")

    response = requests.get(news_api_url)
    if response.status_code == 200:
        print("Response received successfully.")
    else:
        print(f"Failed to fetch news: {response.status_code}")

    data = response.json()
    articles = data.get("results", [])
    return articles

def store_news(db, articles):
    """
    Stores the fetched news articles in a database
    """
    try:
        for article in articles:
            title = article.get("title") or "No Title"
            description = article.get("description") or "No Description"
            db_article = Article(title=title, description=description)
            db.add(db_article)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error storing articles: {e}")
    finally:
        db.close()

def fetch_social_media_posts():
    return []

def parse_news(articles):
    """
    Parses the news articles and sociel media posts and returns a text block 
    """
    # TODO: Implement the logic to parse social media posts
    # and combine them with the news articles
    news_dict = {}
    for article in articles:
        title = article.get("title", "No Title")
        description = article.get("description", "No Description")
        news_dict[title] = description

    combined_text = "\n".join([f"{title}. {desc}" for title, desc in news_dict.items()])
    return combined_text

def generate_trending_word(combined_text):
    """
    Generates trending words using the Groq API.
    """
    # Ensure you have a .env file with GROQ_API_KEY set
    # Example: GROQ_API_KEY=your_groq_api_key

    # Initialize the Groq client with your API key

    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )

    prompt = (
        "নিচের বাংলা লেখাটিতে সবচেয়ে বেশি ব্যবহৃত ১০টি 'বিশেষ্য' (noun) খুঁজে বের করো। "
        "এই শব্দগুলোর তালিকা শুধু বাংলা শব্দ হিসাবে ফেরত দাও, অন্য কিছু লিখো না।\n\n"
        f"{combined_text}\n\n"
        "এরপর, এই লেখার ভিত্তিতে এমন ৫টি শব্দের নাম দাও যেগুলো 'আজকের শব্দ' হিসেবে নির্বাচিত হতে পারে — "
        "অর্থাৎ যেগুলো প্রসঙ্গ অনুযায়ী গুরুত্বপূর্ণ, তাৎপর্যপূর্ণ, বা আলোচ্য। এই শব্দগুলোকেও শুধু বাংলা শব্দ হিসেবে তালিকাভুক্ত করো।"
    )


    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="llama-3.3-70b-versatile",
        stream=False,
    )

    # Output the response
    return chat_completion.choices[0].message.content
