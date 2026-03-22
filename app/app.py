import csv
import os
import uuid
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

CSV_PATH = '/data/requests.csv'
FIELDNAMES = ['id', 'title', 'media_type', 'requested_by', 'notes', 'date_requested', 'status']
_lock = threading.Lock()


def ensure_csv():
    os.makedirs('/data', exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def read_requests():
    ensure_csv()
    with _lock:
        with open(CSV_PATH, 'r', newline='') as f:
            return list(csv.DictReader(f))


def append_request(data):
    ensure_csv()
    with _lock:
        with open(CSV_PATH, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerow(data)


@app.route('/')
def index():
    requests_list = read_requests()
    requests_list.reverse()
    return render_template('index.html', requests=requests_list)


@app.route('/submit', methods=['POST'])
def submit():
    title = request.form.get('title', '').strip()
    if not title:
        return redirect(url_for('index'))
    append_request({
        'id': str(uuid.uuid4())[:8],
        'title': title,
        'media_type': request.form.get('media_type', 'Movie').strip(),
        'requested_by': request.form.get('requested_by', '').strip(),
        'notes': request.form.get('notes', '').strip(),
        'date_requested': datetime.now().strftime('%Y-%m-%d'),
        'status': 'requested',
    })
    return redirect(url_for('index'))
