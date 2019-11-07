from flask import Flask, jsonify
from model import run_news_model

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/news/<string:handle>', methods=['GET'])
def get_news_recommendations(handle: str) -> dict:
    try:
        article = run_news_model(handle)
        return dict(article)
    except Exception as e:
        print(e)
        return {}

@app.route('/tv/<string:handle>', methods=['GET'])
def get_tv_recommendations(handle: str) -> dict:
    try:
        article = run_tv_model(handle)
        return dict(article)
    except Exception as e:
        print(e)
        return {}

if __name__ == '__main__':
    app.run(debug=True)