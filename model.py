import configparser

import numpy as np
import psycopg2
import twitter
from newspaper import Article
from sklearn.feature_extraction.text import TfidfVectorizer

config = configparser.ConfigParser()
config.readfp(open(r"auth.txt"))

# class Recommendation(object):
#     def __init__(self, title, url, similarity_index):
#         self.title = title
#         self.url = url
#         self.similarity_index = similarity_index


def run_news_model(username: str) -> dict:

    print(
        config.get("postgres", "host"),
        config.get("postgres", "user"),
        int(config.get("postgres", "port")),
        config.get("postgres", "password"),
    )

    conn = psycopg2.connect(
        host=config.get("postgres", "host"),
        user=config.get("postgres", "user"),
        port=config.get("postgres", "port"),
        password=config.get("postgres", "password"),
    )
    print(conn)
    cur = conn.cursor()
    print("hello")

    stoplist = [
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "ours",
        "ourselves",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "am",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "a",
        "an",
        "the",
        "and",
        "but",
        "if",
        "or",
        "because",
        "as",
        "until",
        "while",
        "of",
        "at",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "from",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "can",
        "will",
        "just",
        "don",
        "should",
        "now",
        "rt",
        "de",
        "el",
        "la",
        "amp",
        "#",
    ]
    print(cur)
    cur.execute("SELECT tweets, url FROM tweets")
    print("here")
    urls = list()
    text = list()
    for tweets, url in cur:
        urls.append(url)
        text.append(tweets)

    vectorizer = TfidfVectorizer(stop_words=stoplist, min_df=2)

    training_idf = vectorizer.fit_transform(text)
    del text
    print(f"Created training set of {training_idf.shape[0]} urls")

    api = twitter.Api(
        consumer_key=config.get("twitter", "consumer_key"),
        consumer_secret=config.get("twitter", "consumer_secret"),
        access_token_key=config.get("twitter", "access_token_key"),
        access_token_secret=config.get("twitter", "access_token_secret"),
        tweet_mode="extended",
    )
    print(api)

    def get_tweets(user):
        try:
            timeline = api.GetUserTimeline(screen_name=user, count=200)
            print(f"Found {len(timeline)} tweets in timeline")
            text = [tweet.AsDict()["full_text"] for tweet in timeline]
            return " ".join(text)
        except Exception as e:
            print(e)

    user = get_tweets(username)

    query_idf = vectorizer.transform([user])
    similarity = (training_idf * query_idf.T).toarray()
    index = np.nanargmax(similarity)

    while True:
        try:
            article = Article(urls[index])
            article.download()
            article.parse()
            break
        except:
            similarity[index][0] = 0
            index = np.nanargmax(similarity)

    print(f"Similarity is {similarity[index][0]}")
    print(urls[index])
    print(article.title)

    return [
        {
            "article": article.title,
            "url": urls[index],
            "similarity": similarity[index][0],
        }
    ]
