# local_torrent_requests

A minimal local-network web app for submitting and tracking media download requests. Runs in Docker alongside Jellyfin and Portainer.

## What it does

- Submit requests for movies, TV shows, or other media
- View all past requests and their current status
- Status values: `requested` · `in_progress` · `fulfilled` · `not_found`
- Requests are stored in a CSV file at `/home/jesse/docker/torrentreq/data/requests.csv`

## Stack

- **Flask + Gunicorn** — web app (Python 3.12-slim image)
- **dnsmasq** — resolves `http://torrentreq.bug` on the local network (Alpine image)

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

### 2. Configure your router's DNS

For `http://torrentreq.bug` to resolve on all local devices, point your router's **primary DNS server** to this server's LAN IP.

Find your server IP:
```bash
hostname -I
```

Then in your router admin panel (usually `192.168.1.1`):
- DNS Server 1: `<your server IP>`
- DNS Server 2: `8.8.8.8` (fallback)

All DNS queries not matching `torrentreq.bug` are forwarded upstream normally — internet browsing is unaffected.

> **VPN users:** Devices running a VPN will bypass the router DNS and won't resolve `torrentreq.bug`. They can still access the app directly via `http://<server-ip>`.

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
