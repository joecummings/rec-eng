from urllib.parse import urlparse, urljoin
from multiprocessing.pool import ThreadPool
import psycopg2
import requests
import twitter

api = twitter.Api(
    consumer_key="XXX",
    consumer_secret="XXX",
    access_token_key="XXX",
    access_token_secret="XXX",
    tweet_mode="extended",
)

allowlist = {
    "cnn.com",
    "nytimes.com",
    "huffingtonpost.com",
    "foxnews.com",
    "usatoday.com",
    "reuters.com",
    "politico.com",
    "latimes.com",
    "breitbart.com",
    "nypost.com",
    "nbcnews.com",
    "cbsnews.com",
    "abcnews.go.com",
    "chicagotribune.com",
    "wsj.com",
    "buzzfeednews.com",
    "bbc.co.uk",
    "theatlantic.com",
    "vox.com",
    "wired.com",
    "vice.com",
    "theguardian.com",
    "npr.org",
    "time.com",
    "bostonglobe.com",
    "engadget.com",
    "techcrunch.com",
    "sfgate.com",
    "boston.com",
    "freep.com",
    "salon.com",
    "washingtonpost.com",
    "chron.com",
    "tampabay.com",
    "newsday.com",
    "dallasnews.com",
    "nydailynews.com",
    "denverpost.com",
    "seattletimes.com",
    "economist.com",
    "nationalgeographic.com",
    "bloomberg.com",
    "startribune.com",
    "fivethirtyeight.com",
    "dailymail.co.uk",
    "theverge.com",
    "apnews.com",
    "thehill.com",
    "dailycaller.com",
    "telegraph.co.uk",
    "cnbc.com",
    "foxbusiness.com",
}


def strip_params(url):
    return urljoin(url, urlparse(url).path)


def unshorten(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.ok:
            return response.url
    except e:
        print(e)

    return ""


def strip_www(url):
    www = "www."
    if url.startswith(www):
        url = url[len(www) :]
    return url


def is_valid_url(url):
    parsed = urlparse(url)
    if len(parsed.path) < 30:
        return False
    return strip_www(parsed.netloc) in allowlist


def normalize(url):
    url = unshorten(url)
    if is_valid_url(url):
        return strip_params(url)
    return None


def get_tweets(user, count):
    timeline = api.GetUserTimeline(screen_name=user, count=count)
    text = [tweet.AsDict()["full_text"] for tweet in timeline]
    return " ".join(text)


def get_data(url, screen_name, created_at):
    result = dict()
    normalized = normalize(url)
    if normalized is None:
        return None
    print(f"Processing {normalized} {screen_name}")
    tweets = get_tweets(screen_name, 200)
    result["url"] = normalized
    result["username"] = screen_name
    result["tweets"] = tweets
    result["date"] = created_at
    return result


def add_data(result):
    if result is None:
        return
    results.append(result)
    cur.execute(
        "INSERT INTO tweets (date, tweets, url, username) VALUES (%s, %s, %s, %s)",
        (result["date"], result["tweets"], result["url"], result["username"]),
    )
    conn.commit()


conn = psycopg2.connect(host="XXX",
                        user="XXX",
                        port="XXX",
                        password="XXX")
cur = conn.cursor()
results = list()
tweet_count = 0
url_count = 0

stream = api.GetStreamFilter(track=['https'], languages=["en"])

with ThreadPool(processes=10) as pool:
    for tweet in stream:
        if 'user' in tweet:
            tweet_count += 1
            screen_name = tweet['user']['screen_name']
            created_at = tweet['created_at']
            urls = tweet['entities']['urls']
            for url in urls:
                expanded_url = url['expanded_url']
                pool.apply_async(get_data, (expanded_url, screen_name, created_at), callback=add_data)
                if url_count % 250 == 0:
                    print(f"Found {num_found}, "
                          f"processed {tweet_count} tweets ({url_count} urls), "
                          f"skipped {missed}")
                url_count += 1

        elif 'limit' in tweet:
            missed = tweet['limit']['track']

        else:
            print(tweet)