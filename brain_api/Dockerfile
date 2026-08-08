# GeoTutor Python brain (FastAPI): Modes 1 (grounded chat) + 2 (design).
# Build context is the REPOSITORY ROOT (the brain imports src/ and reads
# data/): from the repo root run
#   docker build -f brain_api/Dockerfile .

FROM python:3.11-slim

WORKDIR /app

# system deps kept minimal; matplotlib needs no GUI backend
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    MPLBACKEND=Agg \
    PORT=8000

COPY brain_api/requirements.txt /app/brain_api/requirements.txt
RUN pip install --no-cache-dir -r /app/brain_api/requirements.txt

COPY brain_api /app/brain_api
COPY src /app/src

# The Mode 1 library index (chroma + sqlite, ~2.7 GB) is NOT baked into the
# image. Mount a volume at /app/data and either upload the index to it or
# set INDEX_ARCHIVE_URL to a tar.gz that the entrypoint downloads once.
COPY brain_api/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]
