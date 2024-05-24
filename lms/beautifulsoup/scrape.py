import requests
import keyring
from bs4 import BeautifulSoup
from openai import OpenAI

client = OpenAI(api_key=keyring.get_password("openai", "ask"))


def fetch_latest_news(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('h2')  #, class_='card-headline')
    return [article.get_text() for article in articles[:5]]


def summarize_article(article_text):
    response = client.chat.completions.create(model="gpt-4o",
                                              messages=[{
                                                  "role": "system",
                                                  "content": "Summarize the following article in one paragraph:"
                                              }, {
                                                  "role": "user",
                                                  "content": article_text
                                              }],
                                              max_tokens=100,
                                              n=1)

    return response.choices[0].message.content


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
