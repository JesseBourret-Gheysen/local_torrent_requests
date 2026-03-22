#!/bin/sh
set -e

# Detect the server's outbound LAN IP
HOST_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if ($i=="src") {print $(i+1); exit}}')

if [ -z "$HOST_IP" ]; then
    echo "ERROR: Could not determine server LAN IP" >&2
    exit 1
fi

echo "dnsmasq: torrentreq.bug -> $HOST_IP"
sed "s/SERVER_IP_HERE/$HOST_IP/g" /etc/dnsmasq.conf.template > /etc/dnsmasq.conf
exec dnsmasq --no-daemon --conf-file=/etc/dnsmasq.conf
