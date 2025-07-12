# Stating if a film is bad or good based on it's review
#import nltk 
#from nltk.tokenize import word_tokenize
#from nltk.util import ngrams
#from sklearn.feature_extraction.text import CountVectorizer


# Importing all necessary modeules
import os
import requests
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import transformers
transformers.logging.set_verbosity_error()  # Suppress hugging face logs
from transformers import pipeline

#                                               Load the .env file

load_dotenv()
# Get API key from environment file
API_KEY = os.getenv("TMDB_API_KEY")

#                                               Getting the movie_id
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

#                                                Getting the movie_reviews

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

#                                                   🔍 Ask the user for a movie title
movie_title = input("Enter a movie title: ")
movie_id = get_movie_id(movie_title)

# reviews LIST CONTAIN ALL REVIEWS FOR THE MODEL TRAINING
if movie_id:
    reviews = get_movie_reviews(movie_id, max_reviews=100)  # "reviews" is a list contains all reviews
    print(f"\n✅ Loaded {len(reviews)} reviews for '{movie_title}'")
else:
    print(f"❌ Movie not found, KINDLY EXIT THE PROGRAM BY CLICKING CTRL+C ")


#                                                      Preparing the labels LIST 
labels = []
classifier = pipeline("sentiment-analysis")

def label_review(text): 
    # Truncate to first 512 characters — safe and effective
    truncated = text[:512]    
    result = classifier(truncated)[0]
    return result['label'].lower()

labels = [label_review(review) for review in reviews]


for i in reviews:
    label_review(i) 


#                                                   labels and reviews lists are DONE✅



#                                                          TRAINING THE MODEL

vectorizer = TfidfVectorizer()
x = vectorizer.fit_transform(reviews)
x_train , x_test , y_train , y_test = train_test_split(x , labels , test_size=0.1,random_state=42 )
model = MultinomialNB()
model.fit(x_train , y_train)

#                                                        Taking user's suggestion

user_input = str(input('How do you think movie would be, give an opinion: ')).lower().strip()

user_input2 = str(input('what kind of opinion you gave, positive/negative: ')).lower().strip()

def prediction(user_input,user_input2):
    X = vectorizer.transform([user_input])
    y_pred = model.predict(X)
    accuracy = accuracy_score([user_input2] ,[y_pred[0]])
    if accuracy < 0.65 and user_input2=="positive":
        print(f"Don't waste your money here, gentleman.")
    elif accuracy < 0.65 and user_input2=="negative":
        print(f"But the film has more positive reviews, give it a try")
    elif accuracy >= 0.65 and user_input2=="negative":
        print(f"Don't waste your money here, gentleman.")
    elif accuracy >= 0.65 and user_input2=="positive":
        print(f"Good choice, enjoy your movie")

prediction(user_input,user_input2)
