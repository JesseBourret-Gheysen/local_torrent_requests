import csv
import os
import uuid
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify

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


# --- REST API ---

@app.route('/api/requests', methods=['GET'])
def api_list_requests():
    return jsonify(read_requests())


@app.route('/api/requests/<item_id>', methods=['GET'])
def api_get_request(item_id):
    rows = read_requests()
    row = next((r for r in rows if r['id'] == item_id), None)
    if row is None:
        return jsonify({'error': 'not found'}), 404
    return jsonify(row)


@app.route('/api/requests', methods=['POST'])
def api_create_request():
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'title is required'}), 400
    new_row = {
        'id': str(uuid.uuid4())[:8],
        'title': title,
        'media_type': (data.get('media_type') or 'Movie').strip(),
        'quality': (data.get('quality') or 'any').strip(),
        'audio_language': (data.get('audio_language') or '').strip(),
        'subtitles': 'yes' if data.get('subtitles') else '',
        'requested_by': (data.get('requested_by') or '').strip(),
        'notes': (data.get('notes') or '').strip(),
        'date_requested': datetime.now().strftime('%Y-%m-%d'),
        'status': (data.get('status') or 'requested').strip(),
    }
    append_request(new_row)
    return jsonify(new_row), 201


@app.route('/api/requests/<item_id>', methods=['PUT'])
def api_update_request(item_id):
    data = request.get_json(force=True, silent=True) or {}
    ensure_csv()
    with _lock:
        with open(CSV_PATH, 'r', newline='') as f:
            rows = list(csv.DictReader(f))
        target = next((r for r in rows if r['id'] == item_id), None)
        if target is None:
            return jsonify({'error': 'not found'}), 404
        for field in ['title', 'media_type', 'quality', 'audio_language', 'requested_by', 'notes', 'status']:
            if field in data:
                target[field] = str(data[field]).strip()
        if 'subtitles' in data:
            target['subtitles'] = 'yes' if data['subtitles'] else ''
        with open(CSV_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col, '') for col in FIELDNAMES})
    return jsonify({col: target.get(col, '') for col in FIELDNAMES})


@app.route('/api/requests/media-type/<media_type>', methods=['GET'])
def api_get_requests_by_media_type(media_type):
    rows = [r for r in read_requests()
            if r.get('media_type', '').lower() == media_type.lower()]
    return jsonify(rows)


@app.route('/api/requests/requester/<path:requested_by>', methods=['GET'])
def api_get_requests_by_requester(requested_by):
    q = requested_by.lower()
    rows = [r for r in read_requests()
            if r.get('requested_by', '').lower() == q]
    return jsonify(rows)


@app.route('/api/requests/title/<path:query>', methods=['GET'])
def api_get_requests_by_title(query):
    q = query.lower()
    rows = [r for r in read_requests()
            if q in r.get('title', '').lower()]
    return jsonify(rows)


@app.route('/api/requests/<item_id>', methods=['DELETE'])
def api_delete_request(item_id):
    ensure_csv()
    with _lock:
        with open(CSV_PATH, 'r', newline='') as f:
            rows = list(csv.DictReader(f))
        original_len = len(rows)
        rows = [r for r in rows if r['id'] != item_id]
        if len(rows) == original_len:
            return jsonify({'error': 'not found'}), 404
        with open(CSV_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col, '') for col in FIELDNAMES})
    return ('', 204)
