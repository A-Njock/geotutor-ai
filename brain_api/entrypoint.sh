#!/bin/sh
# GeoTutor brain entrypoint: fetch the Mode 1 library index into the mounted
# volume on first boot (optional), then serve.

set -e

DATA_DIR="${DATA_DIR:-/app/data}"

# one-time recovery switch: wipe the volume and re-download a clean index
if [ -n "$INDEX_FORCE_REFRESH" ]; then
    echo "[boot] INDEX_FORCE_REFRESH set: clearing $DATA_DIR ..."
    rm -rf "$DATA_DIR"/* "$DATA_DIR"/.index_ready 2>/dev/null || true
fi

if [ -n "$INDEX_ARCHIVE_URL" ] && [ ! -e "$DATA_DIR/.index_ready" ]; then
    echo "[boot] downloading library index into $DATA_DIR ..."
    mkdir -p "$DATA_DIR"
    # the archive must contain the contents of the local data/ folder
    curl -L --fail "$INDEX_ARCHIVE_URL" | tar xz -C "$DATA_DIR"
    touch "$DATA_DIR/.index_ready"
    echo "[boot] index ready."
fi

exec uvicorn brain_api.main:api --host 0.0.0.0 --port "${PORT:-8000}"
