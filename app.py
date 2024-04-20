from flask import Flask, render_template, request, url_for, redirect , jsonify
from urllib.robotparser import RobotFileParser
from scraper import scrape_tos
from datetime import datetime
import mysql.connector
import json

app = Flask(__name__, template_folder=r'C:\Users\bhanu\Desktop\net_crawler\scrape\templates')

db_config = {
    'user': 'root',
    'password': 'mysql',
    'host': '127.0.0.1:3306',
    'database': 'tosdatabase'
}

def get_db_connection():
    """Establish a connection to the database."""
    return mysql.connector.connect(**db_config)


@app.route('/')
def home():
    """Render the homepage."""
    return render_template('index.html')

def is_allowed_to_scrape(url):
    """Check if scraping the URL is allowed by robots.txt."""
    robot_parser = RobotFileParser()
    robot_parser.set_url(url + '/robots.txt')
    robot_parser.read()
    return robot_parser.can_fetch("*", url)

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    if url:
        if is_allowed_to_scrape(url):
            data = scrape_tos(url)
            return jsonify({"status": "success", "data": data}), 200
        else:
            return jsonify({"status": "error", "message": "Scraping this URL is disallowed by robots.txt"}), 403
    return jsonify({"status": "error", "message": "URL is required"}), 400

def save_tos_data(url, tos_text):    
    data = {
        "tos": tos_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        
        with open('tos_data.json', 'r', encoding='utf-8') as file:
            tos_data = json.load(file)
            if not isinstance(tos_data, dict):
                raise json.JSONDecodeError("Data is not a dictionary", doc=file, pos=0)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        tos_data = {}

    tos_data[url] = data

    with open('tos_data.json', 'w', encoding='utf-8') as file:
        json.dump(tos_data, file, indent=4, ensure_ascii=False)


        
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        tos_text = scrape_tos(url) 
        save_tos_data(url, tos_text)
        return redirect(url_for('display_tos', url=url))
    return render_template('index.html')


@app.route('/display_tos')
def display_tos():
    url = request.args.get('url')
    try:
        with open('tos_data.json', 'r', encoding='utf-8') as file:
            tos_data = json.load(file)
        current_tos = tos_data.get(url, {"tos": "No ToS found for this URL.", "timestamp": ""})
    except (FileNotFoundError, json.JSONDecodeError):
        current_tos = {"tos": "No ToS data available.", "timestamp": ""}
    return render_template('display_tos.html', url=url, tos=current_tos)


@app.route('/stored_tos')
def stored_tos():
    try:
        with open('tos_data.json', 'r', encoding='utf-8') as file:
            tos_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        tos_data = {}
    return render_template('stored_tos.html', tos_data=tos_data)

if __name__ == '__main__':
    app.run(debug=True)
