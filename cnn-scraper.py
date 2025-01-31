from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
import logging
from datetime import datetime
import re # regular expression


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
        
        if headlines_to_process:
            for headline in headlines_to_process:
                title = headline.text
                article_url = headline.find_parent('a')['href']

                if not article_url.startswith('http'):
                    article_url = requests.compat.urljoin(url, article_url)

                article_response = requests.get(article_url)
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                content = article_soup.find('div', class_='article__content')
                
                # Extracting image URL
                image_div = article_soup.find('div', class_='image')
                image_url = image_div.find('img', class_='image__dam-img')['src'] if image_div else None
                
                # Inside your loop
                byline = article_soup.find('div', class_='byline__names')
                authors = byline.text.strip() if byline else "Unknown Author"

                read_duration_div = article_soup.find('div', class_='headline__sub-description')
                read_duration = read_duration_div.text.strip() if read_duration_div else "Unknown Duration"

                timestamp = article_soup.find('div', class_='timestamp')
                if timestamp:
                    timestamp_text = timestamp.text.strip()
                    # Look for either 'Published' or 'Updated' in the timestamp text
                    if 'Published' in timestamp_text:
                        inspected_date = timestamp_text.split('Published', 1)[1].strip()
                    elif 'Updated' in timestamp_text:
                        inspected_date = timestamp_text.split('Updated', 1)[1].strip()
                    else:
                        inspected_date = "Unknown Date"
                else:
                    inspected_date = "Unknown Timestamp"
                if content:
                    articles.append({
                        'title': title,
                        'content': content.text.strip(),
                        'image': image_url,
                        'authors': authors,
                        'read_duration': read_duration,
                        'date_inspected': inspected_date
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
