import configparser
import time
import numpy as np
import psycopg2
import twitter
from newspaper import Article
from sklearn.feature_extraction.text import TfidfVectorizer

config = configparser.ConfigParser()
config.read_file(open(r"auth.txt"))
conn = psycopg2.connect(
    host=config["postgres"]["host"],
    user=config["postgres"]["user"],
    port=config["postgres"]["port"],
    password=config["postgres"]["password"],
)
cur = conn.cursor()
print("Finished connecting to database")

with open("stoplist.txt") as f:
    stoplist = f.read().splitlines()
print("Loaded stoplist")

vectorizer = None
training_idf = None
urls = None


def reload_model():
    global vectorizer, training_idf, urls
    print("Reloading model")
    start_time = time.time()
    cur.execute("SELECT tweets, url FROM tweets ORDER BY(date) DESC LIMIT 10000")
    new_urls = list()
    new_text = list()
    for tweets, url in cur:
        new_urls.append(url)
        new_text.append(tweets)
    print(
        f"Loaded {len(new_urls)} tweets from database in {time.time() - start_time} seconds"
    )

    start_time = time.time()
    new_vectorizer = TfidfVectorizer(stop_words=stoplist, min_df=2)
    print(f"Trained vectorizer in {time.time() - start_time} seconds")

    start_time = time.time()
    new_training_idf = new_vectorizer.fit_transform(new_text)
    print(
        f"Created idf with shape {new_training_idf.shape} in {time.time() - start_time} seconds"
    )

    del new_text
    vectorizer, training_idf, urls = new_vectorizer, new_training_idf, new_urls


reload_model()

api = twitter.Api(
    consumer_key=config.get("twitter", "consumer_key"),
    consumer_secret=config.get("twitter", "consumer_secret"),
    access_token_key=config.get("twitter", "access_token_key"),
    access_token_secret=config.get("twitter", "access_token_secret"),
    tweet_mode="extended",
)
print("Connected to the twitter API. Ready to process requests.")


def get_tweets(user):
    timeline = api.GetUserTimeline(screen_name=user, count=200)
    print(f"Found {len(timeline)} tweets in timeline")
    text = [tweet.AsDict()["full_text"] for tweet in timeline]
    return " ".join(text)


def run_news_model(username: str) -> dict:
    user = get_tweets(username)
    query_idf = vectorizer.transform([user])
    similarity = (training_idf * query_idf.T).toarray()
    index = int(np.nanargmax(similarity))

    results = list()
    for _ in range(3):
        while True:
            try:
                article = Article(urls[index])
                article.download()
                article.parse()
                break
            except Exception as e:
                print(e)
                similarity[index][0] = 0
                index = int(np.nanargmax(similarity))

        print(f"Similarity is {similarity[index][0]}")
        print(urls[index])
        print(article.title)
        print(article.top_image)

        item = {
            "title": article.title,
            "image": article.top_image,
            "url": urls[index],
            "similarity": similarity[index][0],
        }

        results.append(item)

        similarity[index][0] = 0
        index = int(np.nanargmax(similarity))

    return results
