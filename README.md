# local_torrent_requests

A minimal local-network web app for submitting and tracking media download requests. Runs in Docker alongside Jellyfin and Portainer.

## What it does

- Submit requests for movies, TV shows, or other media
- View all past requests and their current status
- Status values: `requested` · `in_progress` · `fulfilled` · `not_found`
- Requests are stored in a CSV file at `/home/jesse/docker/torrentreq/data/requests.csv`

## Stack

- **Flask + Gunicorn** — web app (Python 3.12-slim image)
- **dnsmasq** — resolves `http://torrentreq.bug` on the local network — runs as a separate container, see [local_dnsmasq](https://github.com/JesseBourret-Gheysen/local_dnsmasq)

---

## First-time setup

### 1. Build and start

```bash
docker compose -f /home/jesse/Documents/local_torrent_requests/docker-compose.yml up -d --build
```

Or use the full stack script (builds everything):

```bash
sudo /home/jesse/docker/start-all.sh
```

The data directory `/home/jesse/docker/torrentreq/data/` is created automatically on first run.

### 2. Set up local DNS (optional)

For `http://torrentreq.bug` to resolve on all local devices, deploy the companion [local_dnsmasq](https://github.com/JesseBourret-Gheysen/local_dnsmasq) container and point your router's DNS at this server. Full instructions are in that repo's README.

Without it, the app is still accessible via direct IP: `http://<server-ip>`.

### 3. Access

| Method | URL |
|--------|-----|
| Local domain (after DNS setup) | `http://torrentreq.bug` |
| Direct IP (always works) | `http://<server-ip>` |

---

## CSV file

Requests are stored at:
```
/home/jesse/docker/torrentreq/data/requests.csv
```

Columns: `id, title, media_type, requested_by, notes, date_requested, status`

The `status` column can be updated directly in the CSV or by another app. Valid values: `requested`, `in_progress`, `fulfilled`, `not_found`.

---

## Managing the containers

```bash
# Start
docker compose -f /home/jesse/Documents/local_torrent_requests/docker-compose.yml up -d

# Stop
docker compose -f /home/jesse/Documents/local_torrent_requests/docker-compose.yml down

# Rebuild after code changes
docker compose -f /home/jesse/Documents/local_torrent_requests/docker-compose.yml up -d --build

# View app logs
docker logs -f torrentreq

# View DNS logs
docker logs -f dnsmasq_torrentreq
```

---

## REST API

All endpoints are under `/api/requests`. Responses are JSON. No authentication required (local network only).

### CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/requests` | List all requests |
| GET | `/api/requests/<id>` | Get a single request by ID |
| POST | `/api/requests` | Create a new request |
| PUT | `/api/requests/<id>` | Update an existing request |
| DELETE | `/api/requests/<id>` | Delete a request (returns 204) |

### Filtered GET endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/requests/media-type/<media_type>` | All requests matching a media type exactly (case-insensitive). e.g. `/api/requests/media-type/Movie` |
| GET | `/api/requests/requester/<name>` | All requests from a specific person (exact match, case-insensitive). e.g. `/api/requests/requester/jesse` |
| GET | `/api/requests/title/<query>` | All requests whose title contains the query string (case-insensitive substring). e.g. `/api/requests/title/dark knight` |

### Request body fields (POST / PUT)

| Field | Required | Notes |
|-------|----------|-------|
| `title` | Yes (POST) | Media title |
| `media_type` | No | e.g. `Movie`, `TV`, `Other` (default: `Movie`) |
| `quality` | No | e.g. `1080p`, `4K`, `any` (default: `any`) |
| `audio_language` | No | e.g. `English` |
| `subtitles` | No | `true`/`false` |
| `requested_by` | No | Person's name |
| `notes` | No | Additional notes |
| `status` | No | `requested`, `in_progress`, `fulfilled`, `not_found` (default: `requested`) |

### Response object

```json
{
  "id": "a1b2c3d4",
  "title": "The Dark Knight",
  "media_type": "Movie",
  "quality": "1080p",
  "audio_language": "English",
  "subtitles": "",
  "requested_by": "jesse",
  "notes": "",
  "date_requested": "2026-04-07",
  "status": "requested"
}
```

`subtitles` is `"yes"` when requested, `""` when not.

---

## Troubleshooting

**Port 80 already in use**
```bash
sudo ss -tlnp | grep ':80'
```
Stop whatever is using port 80, or change the host port in `docker-compose.yml` (e.g. `"8080:80"`) and access via `http://<server-ip>:8080`.

**Port 53 conflict (dnsmasq won't start)**
```bash
sudo ss -ulnp | grep ':53'
```
If `systemd-resolved` is using port 53 on the LAN interface, disable its stub listener:
```bash
sudo sed -i 's/#DNSStubListener=yes/DNSStubListener=no/' /etc/systemd/resolved.conf
sudo systemctl restart systemd-resolved
```

**`torrentreq.bug` not resolving on a device**
1. Confirm the device's DNS is set to the server IP (check router settings or device network config)
2. Flush DNS cache on the device: `ipconfig /flushdns` (Windows) or `sudo systemd-resolve --flush-caches` (Linux)
3. Check dnsmasq is running: `docker ps | grep dnsmasq`
