# GeoTutor Brain API

FastAPI wrapper for the Python multi-agent brain system.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Make sure parent dependencies are installed
cd ..
pip install -r requirements.txt  # Your existing LanGraph dependencies

# 3. Run the API
cd brain_api
python main.py
```

The API will start on `http://localhost:8000`

## Endpoints

- `GET /` - Health check
- `POST /ask` - Ask a question (main endpoint)
- `POST /generate-exam` - Generate exam materials
- `GET /system/info` - Get system information

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Request

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain soil consolidation",
    "includeVisual": false
  }'
```

## Environment Variables

Create a `.env` file in the parent directory with:
```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```
