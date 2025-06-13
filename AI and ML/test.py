#working on machine learning

import nltk 
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import random

# Categories
tech_sentences = [
    "Python is great for data science.",
    "AI is transforming industries.",
    "Quantum computing will change the future.",
    "Just installed Linux on my PC.",
    "TensorFlow and PyTorch are deep learning frameworks.",
    "The new iPhone has a better processor.",
    "Learning React for front-end dev.",
    "My GPU can't handle the latest models.",
    "GitHub Copilot helps me code faster.",
    "Docker makes deployment easier.",
    "I love writing scripts in Bash.",
    "Stack Overflow is down again!",
    "My server crashed last night.",
    "Fixed a bug in my Python script.",
    "Debugging machine learning models is hard.",
    "Trying out GPT-4's new features.",
    "Learned about transformers in NLP today.",
    "Selenium automates browser tasks.",
    "Set up an API with Flask.",
    "My model is overfitting badly.",
    "What's the best IDE for C++?",
    "Got a bug in my backend code.",
    "Chrome DevTools are so useful.",
    "Finally deployed my app to Heroku.",
    "Studying computer architecture.",
    "Learning SQL joins is tough.",
    "TensorBoard helps me visualize training.",
    "Upgraded my RAM to 32GB.",
    "Reading about reinforcement learning.",
    "Installed Kali Linux for pen testing."
]

non_tech_sentences = [
    "The movie was amazing!",
    "Just came back from a hike.",
    "Making pancakes for breakfast.",
    "Traffic is so bad today.",
    "Had a great workout this morning.",
    "The weather is so nice outside.",
    "Watching the sunset with friends.",
    "Reading a new mystery novel.",
    "Went shopping at the mall.",
    "My cat is acting weird today.",
    "Can't stop listening to this song.",
    "This new café has great coffee.",
    "Baking cookies tonight.",
    "Forgot my umbrella, got soaked.",
    "Planning a road trip next week.",
    "Missed my bus by 2 minutes.",
    "Trying to eat healthy now.",
    "That was a beautiful painting.",
    "Got a new plant for my room.",
    "Going to a wedding tomorrow.",
    "Heard a weird noise at night.",
    "The party was so much fun.",
    "Painting my bedroom walls.",
    "That book made me cry.",
    "Wore mismatched socks today.",
    "Took a nap for 3 hours.",
    "Learned to juggle today!",
    "This playlist is fire.",
    "Had the best pizza ever.",
    "Trying to learn guitar chords."
]

# Add real-world "noise"
noisy_endings = ["!!!", "lol", "idk", "💀", "huh?", "ikr", "so weird", "bruh", "wtf", "no cap"]
noisy_words = ["Tensorflw", "machne learnin", "deplyoment", "ideaa", "tranning", "procssor", "lptop", "ml modelz", "np api", "guitr"]

# Mix clean and noisy data
texts = []
labels = []
for _ in range(150):
    s = random.choice(tech_sentences)
    if random.random() < 0.3:  # Add noise 30% of time
        s = s.replace("learning", random.choice(noisy_words))
        s += " " + random.choice(noisy_endings)
    texts.append(s)
    labels.append("tech")

for _ in range(150):
    s = random.choice(non_tech_sentences)
    if random.random() < 0.3:
        s = s.replace("pizza", random.choice(noisy_words))
        s += " " + random.choice(noisy_endings)
    texts.append(s)
    labels.append("non-tech")

# Shuffle to simulate real-world randomness
combined = list(zip(texts, labels))
random.shuffle(combined)
texts, labels = zip(*combined)


def accu(texts, labels , rnd):
    vectorizer = TfidfVectorizer()
    x = vectorizer.fit_transform(texts)      #creates a matrix of words and it's count in dataset

    x_train , x_test , y_train , y_test = train_test_split(x , labels , test_size=0.2,random_state=rnd )
    model = MultinomialNB()
    model.fit(x_train , y_train)

    y_pred = model.predict(x_test)
    accuracy = accuracy_score(y_test , y_pred)
    print(f"Accuracy: {accuracy}")

for i in range(0,50):
    accu(texts, labels,i)

