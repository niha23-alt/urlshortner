from flask import Flask, render_template, request, redirect
import sqlite3
import os
from nanoid import generate
from urllib.parse import urlparse

app = Flask(__name__)


def init_db():
    if not os.path.exists('url_data.db'):
        with sqlite3.connect('url_data.db') as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_url TEXT NOT NULL,
                    short_code TEXT NOT NULL UNIQUE,
                    click_count INTEGER DEFAULT 0
                )
            ''')


def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.scheme) and bool(parsed.netloc)


def generate_unique_short_code():
    with sqlite3.connect('url_data.db') as conn:
        while True:
            short_code = generate(size=7)
            cursor = conn.execute("SELECT 1 FROM urls WHERE short_code = ?", (short_code,))
            if not cursor.fetchone():
                return short_code


@app.route('/', methods=['GET', 'POST'])
def home():
    short_url = None
    error_message = None
    click_count = None
    if request.method == 'POST':
        original_url = request.form['original_url'].strip()

        if not is_valid_url(original_url):
            error_message = "Please enter a valid URL including http:// or https://"
        else:
            with sqlite3.connect('url_data.db') as conn:
                cursor = conn.execute("SELECT short_code, click_count FROM urls WHERE original_url = ?", (original_url,))
                result = cursor.fetchone()

                if result:
                    short_code,click_count = result
                else:
                    short_code = generate_unique_short_code()
                    conn.execute("INSERT INTO urls (original_url, short_code) VALUES (?, ?)", (original_url, short_code))
                    click_count=0
                short_url = request.host_url + short_code

    return render_template('index.html', short_url=short_url, error=error_message,click_count=click_count)


@app.route('/<short_code>')
def redirect_short_url(short_code):
    with sqlite3.connect('url_data.db') as conn:
        cursor = conn.execute("SELECT original_url FROM urls WHERE short_code = ?", (short_code,))
        result = cursor.fetchone()
        if result:
            conn.execute("UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?", (short_code,)),
            return redirect(result[0])
    return "Invalid or expired short URL", 404


if __name__ == '__main__':
    init_db()
    app.run(debug=True)