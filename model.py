from sklearn.feature_extraction.text import TfidfVectorizer
from newspaper import Article
import numpy as np
import psycopg2
import twitter

# class Recommendation(object):
#     def __init__(self, title, url, similarity_index):
#         self.title = title
#         self.url = url
#         self.similarity_index = similarity_index


def run_news_model(username: str) -> dict:

    conn = psycopg2.connect(host="rec-eng.c3nw6fvutjah.us-east-1.rds.amazonaws.com",
                            user="postgres",
                            port=1234,
                            password="fuckthegarage")
    cur = conn.cursor()

    stoplist = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself",
                "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself",
                "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
                "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
                "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as",
                "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through",
                "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off",
                "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how",
                "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not",
                "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should",
                "now", "rt", "de", "el", "la", "amp", "#"]

    cur.execute("SELECT tweets, url FROM tweets")

    urls = list()
    text = list()
    for tweets, url in cur:
        urls.append(url)
        text.append(tweets)

    vectorizer = TfidfVectorizer(stop_words=stoplist, min_df=2)

    training_idf = vectorizer.fit_transform(text)
    del text
    print(f"Created training set of {training_idf.shape[0]} urls")

    api = twitter.Api(consumer_key='xea26XfYEJV34VPztm8oGfn5E',
                    consumer_secret='evA1msunGgC5k4JlyhQVNnJl9SSD6QA0iEbc6gkOMHWyszoWVf',
                    access_token_key='3734537962-0btTrrB2Kb6ATHlRtrS19iLVr0pIdA5XsIaXJFt',
                    access_token_secret='a3r1w1lgXg0MQiuQ68HSbz3B4V8cEj9Y0nfkGkmBxbLbb',
                    tweet_mode='extended')

    def get_tweets(user):
        try:
            timeline = api.GetUserTimeline(screen_name=user, count=200)
            print(f"Found {len(timeline)} tweets in timeline")
            text = [tweet.AsDict()['full_text'] for tweet in timeline]
            return " ".join(text)
        except Exception as e:
            print(e)

    user = get_tweets(username) # right here

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

    return {
        "article": article.title, 
        "url": urls[index], 
        "similarity": similarity[index][0]
    }
