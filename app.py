from flask import Flask, jsonify
from flask_cors import CORS

from model import run_news_model

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return "Hello, World!"


@app.route("/api/dummy_endpoint", methods=["GET"])
def get_dummy() -> list:
    return jsonify(
        {"title": "test1", "url": "http://google.com", "score": 0.5},
        {"title": "test2", "url": "http://google.com", "score": 0.4},
        {"title": "test3", "url": "http://google.com", "score": 0.2},
    )


@app.route("/news/<string:handle>", methods=["GET"])
def get_news_recommendations(handle: str) -> list:
    try:
        articles = run_news_model(handle)
        return jsonify(articles)
    except Exception as e:
        print(e)
        return jsonify([])


@app.route("/tv/<string:handle>", methods=["GET"])
def get_tv_recommendations(handle: str) -> list:
    try:
        shows = run_tv_model(handle)
        return jsonify(shows)
    except Exception as e:
        print(e)
        return jsonify([])


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
