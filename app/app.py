import csv
import os
import uuid
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

CSV_PATH = '/data/requests.csv'
FIELDNAMES = [
    'id', 'title', 'media_type', 'quality', 'audio_language', 'subtitles',
    'requested_by', 'notes', 'date_requested', 'status',
]
_lock = threading.Lock()


def ensure_csv():
    os.makedirs('/data', exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()
        return
    # Migrate existing CSV if new columns are missing
    with open(CSV_PATH, 'r', newline='') as f:
        existing_fields = csv.DictReader(f).fieldnames or []
    if any(col not in existing_fields for col in FIELDNAMES):
        with open(CSV_PATH, 'r', newline='') as f:
            rows = list(csv.DictReader(f))
        with open(CSV_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in rows:
                for col in FIELDNAMES:
                    row.setdefault(col, '')
                writer.writerow({col: row[col] for col in FIELDNAMES})


def read_requests():
    ensure_csv()
    with _lock:
        with open(CSV_PATH, 'r', newline='') as f:
            rows = list(csv.DictReader(f))
    for row in rows:
        for col in FIELDNAMES:
            row.setdefault(col, '')
    return rows


def append_request(data):
    ensure_csv()
    with _lock:
        with open(CSV_PATH, 'a', newline='') as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(data)


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
        'quality': request.form.get('quality', 'any').strip(),
        'audio_language': request.form.get('audio_language', '').strip(),
        'subtitles': 'yes' if request.form.get('subtitles') == 'on' else '',
        'requested_by': request.form.get('requested_by', '').strip(),
        'notes': request.form.get('notes', '').strip(),
        'date_requested': datetime.now().strftime('%Y-%m-%d'),
        'status': 'requested',
    })
    return redirect(url_for('index'))
