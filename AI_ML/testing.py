import os
import requests
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")

def get_movie_id(title):
    """Get the TMDb movie ID for a given movie title."""
    url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": API_KEY, "query": title}
    response = requests.get(url, params=params).json()

    results = response.get('results')
    if results:
        return results[0]['id']
    else:
        return None


def get_movie_reviews(movie_id, max_reviews=100):
    """Fetch up to `max_reviews` from TMDb for a given movie ID."""

    all_reviews = []
    page = 1

    while len(all_reviews) < max_reviews:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews"
        params = {"api_key": API_KEY, "language": "en-US", "page": page}
        response = requests.get(url, params=params).json()
        reviews = response.get("results", [])

        if not reviews:
            break  # No more reviews

        all_reviews.extend([r['content'] for r in reviews])
        page += 1

    return all_reviews[:max_reviews]

# 🔍 Ask the user for a movie title
movie_title = input("Enter a movie title: ")
movie_id = get_movie_id(movie_title)

if movie_id:
    reviews = get_movie_reviews(movie_id, max_reviews=100)
    print(f"\n✅ Loaded {len(reviews)} reviews for '{movie_title}'")
else:
    print(f"❌ Movie not found, KINDLY EXIT THE PROGRAM BY CLICKING CTRL+C ")

for i in reviews:
    print(i)