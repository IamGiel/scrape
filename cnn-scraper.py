from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
import logging
from datetime import datetime
import re

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.ERROR)

@app.route('/api/articles', methods=['GET'])
def get_articles():
    try:
        page = int(request.args.get('page', 1))  # Default to page 1 if not specified
        per_page = int(request.args.get('per_page', 20))  # Default to 20 articles per page if not specified

        url = "https://edition.cnn.com/world"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # All headlines
        headlines = soup.select('span.container__headline-text')
        
        # Slice headlines based on pagination
        start = (page - 1) * per_page
        end = start + per_page
        headlines_to_process = headlines[start:end]

        articles = []
        for headline in headlines_to_process:
            title = headline.text
            parent = headline.find_parent('a')
            article_url = parent['href'] if parent else None

            if not article_url.startswith('http'):
                article_url = requests.compat.urljoin(url, article_url)

            article_response = requests.get(article_url)
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            content = article_soup.find('div', class_='article__content')
            
            image_div = article_soup.find('div', class_='image')
            image_url = None
            if image_div:
                img = image_div.find('img', class_='image__dam-img')
                if img:
                    image_url = img.get('src')

            byline = article_soup.find('div', class_='byline__names')
            authors = byline.text.strip() if byline else "Unknown Author"

            read_duration_div = article_soup.find('div', class_='headline__sub-description')
            read_duration = read_duration_div.text.strip() if read_duration_div else "Unknown Duration"

            timestamp = article_soup.find('div', class_='timestamp')
            inspected_date = "Unknown Timestamp"
            if timestamp:
                timestamp_text = timestamp.text.strip()
                if 'Published' in timestamp_text:
                    inspected_date = timestamp_text.split('Published', 1)[1].strip()
                elif 'Updated' in timestamp_text:
                    inspected_date = timestamp_text.split('Updated', 1)[1].strip()

            if content:
                articles.append({
                    'notificationId': str(hash(title)),  # Creating a unique ID from title
                    'title': title,
                    'description': content.text.strip()[:200] + "..." if len(content.text.strip()) > 200 else content.text.strip(),  # Limit description to 200 chars for brevity
                    'publicationDate': inspected_date,
                    'author':authors,
                    'img':image_url
                })
        else: 
            print('NO HEADLINES') 

        return jsonify(articles)

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request exception: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

if __name__ == '__main__':
    app.run(port=9002, debug=True)