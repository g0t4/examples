import os
import keyring
import openai
import requests
from bs4 import BeautifulSoup

openai.api_key = keyring.get_password("openai", "ask")


def fetch_latest_news(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('h2')#, class_='card-headline')
    return [article.get_text() for article in articles[:5]]  # Get the first 5 articles


def summarize_article(article_text):
    response = openai.Completion.create(model="text-davinci-003", prompt=f"Summarize the following article in one paragraph:\n\n{article_text}", max_tokens=100)
    summary = response.choices[0].text.strip()
    return summary


def main():
    news_url = "https://www.bbc.com/news"
    articles = fetch_latest_news(news_url)
    print(articles)

    for i, article in enumerate(articles):
        summary = summarize_article(article)
        print(f"Article {i+1}: {article}")
        print(f"Summary: {summary}\n")


if __name__ == "__main__":
    main()
