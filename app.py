from flask import Flask, render_template, request, jsonify
from selenium_scraper import get_tos_content  
from flask_mysqldb import MySQL
from datetime import datetime
import hashlib
import requests

app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mysql'
app.config['MYSQL_DB'] = 'tosdatabase'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/stored_tos')
def stored_tos():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT terms_of_service.tos_id, websites.url, terms_of_service.content, terms_of_service.date_recorded
        FROM terms_of_service
        JOIN websites ON terms_of_service.website_id = websites.website_id
    """)
    stored_tos_entries = cursor.fetchall()
    cursor.close()
    return render_template('stored_tos.html', tos_entries=stored_tos_entries)

@app.route('/archive_tos', methods=['GET', 'POST'])
def archive_tos():
    message = ''
    archived_tos_entries = []  # Initialize as empty list to handle cases where no data is fetched

    if request.method == 'POST':
        tos_id = request.form.get('tos_id')
        content = request.form.get('content')
        
        if not tos_id or not content:
            message = 'No ToS ID or content provided'
        else:
            tos_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            cursor = mysql.connection.cursor()

            # Check if the hash exists in the archive table
            cursor.execute("SELECT content_hash FROM archive_tos WHERE content_hash = %s", (tos_hash,))
            if cursor.fetchone() is None:
                # If not, insert it into the archive table
                cursor.execute("""
                    INSERT INTO archive_tos (tos_id, content, content_hash, date_recorded)
                    VALUES (%s, %s, %s, NOW())
                """, (tos_id, content, tos_hash))
                mysql.connection.commit()
                message = 'Content archived successfully!'
            else:
                message = 'Content is already archived.'

            cursor.close()

    # Fetch all archive entries regardless of the POST method result
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT at.archive_id, at.date_recorded, at.content_hash, ts.content as terms_content, w.url
        FROM archive_tos at
        JOIN terms_of_service ts ON at.tos_id = ts.tos_id
        JOIN websites w ON ts.website_id = w.website_id
    """)
    archived_tos_entries = cursor.fetchall()
    cursor.close()
    
    return render_template('archive_tos.html', archives=archived_tos_entries, message=message)



@app.route('/submit_url', methods=['POST'])
def submit_url():
    url = request.form['url']
    message = 'No Terms of Service processed.'
    tos_text = get_tos_content(url)
    current_time = datetime.now()
    cursor = mysql.connection.cursor()
    
    # Check if the website already exists and retrieve its ID
    cursor.execute("SELECT website_id FROM websites WHERE url = %s", (url,))
    website_row = cursor.fetchone()
    
    if website_row:
        website_id = website_row['website_id']
        # Update the last scraped time
        cursor.execute("UPDATE websites SET last_scraped = %s WHERE website_id = %s", (current_time, website_id))
    else:
        # Insert the new website and get the new website_id
        cursor.execute("INSERT INTO websites (url, last_scraped) VALUES (%s, %s)", (url, current_time))
        website_id = cursor.lastrowid
        
    mysql.connection.commit()
    
    if tos_text:
        tos_hash = hashlib.sha256(tos_text.encode('utf-8')).hexdigest()
        # Fetch existing terms of service entry
        cursor.execute("SELECT tos_id, content, content_hash FROM terms_of_service WHERE website_id = %s", (website_id,))
        existing = cursor.fetchone()
    
        if existing:
            current_tos_id = existing['tos_id']
            current_content = existing['content']
            current_hash = existing['content_hash']

            # Archive previous content if hash is different
            if tos_hash != current_hash:
                cursor.execute("""
                    INSERT INTO archive_tos (tos_id, content, content_hash, date_recorded)
                    VALUES (%s, %s, %s, NOW())
                """, (current_tos_id, current_content, current_hash))
                mysql.connection.commit()
                message = 'Terms of Service content has changed and the previous version was archived.'

            # Update existing Terms of Service entry
            cursor.execute("""
                UPDATE terms_of_service SET content = %s, content_hash = %s, date_recorded = %s
                WHERE tos_id = %s
            """, (tos_text, tos_hash, current_time, current_tos_id))
            mysql.connection.commit()
        else:
            # Insert new Terms of Service entry
            cursor.execute("""
                INSERT INTO terms_of_service (website_id, content, content_hash, date_recorded)
                VALUES (%s, %s, %s, %s)
            """, (website_id, tos_text, tos_hash, current_time))
            message = 'Terms of Service saved successfully!'
        mysql.connection.commit()
    else:
        message = 'Terms of Service not found.'

    cursor.close()
    return render_template('scrape_result.html', url=url, content=tos_text if tos_text else '', time_scraped=current_time, message=message)


@app.route('/tos_details/<int:tos_id>')
def tos_details(tos_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM terms_of_service WHERE tos_id = %s", (tos_id,))
    entry = cursor.fetchone()
    cursor.close()
    if entry:
        return render_template('tos_details.html', entry=entry)
    else:
        return "ToS entry not found.", 404
    
@app.route('/archive_details/<int:archive_id>')
def archive_details(archive_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM archive_tos WHERE archive_id = %s", (archive_id,))
    archive_entry = cursor.fetchone()
    cursor.close()
    if archive_entry:
        return render_template('archive_details.html', entry=archive_entry)
    else:
        return "Archived ToS entry not found.", 404


def can_scrape_site(url):
    """ Check if scraping a website is allowed based on its robots.txt. """
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = f"{base_url}/robots.txt"
    try:
        response = requests.get(robots_url)
        response.raise_for_status()
        lines = response.text.splitlines()
        for line in lines:
            if line.startswith('User-agent: *'):
                # Start recording rules for all bots
                for rule in lines[lines.index(line):]:
                    if rule.startswith('Disallow: '):
                        disallowed_path = rule.split(' ')[1].strip()
                        if disallowed_path == '/' or url.startswith(f"{base_url}{disallowed_path}"):
                            return False
        return True
    except requests.RequestException:
        return False  # Assume false if there's any issue retrieving the robots.txt
    
if __name__ == '__main__':
    app.run(debug=True)
