# GeoTutor Integration Testing Guide

##  Quick Start (All Services)

### 1. Start Python Brain API

```bash
# Terminal 1: Python Brain
cd e:\YORK.A\Python codes2\Antigrav\brain_api
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install -r ../requirements.txt  # Install your existing LanGraph dependencies
python main.py
```

Brain will run on: `http://localhost:8000`

### 2. Start TypeScript Backend (Already Running!)

Your TypeScript backend is already running in the background.
It's on: `http://localhost:3000`

### 3. Start React Frontend

```bash
# Terminal 3: React Frontend
cd e:\YORK.A\Python codes2\Antigrav\geotutor
pnpm dev
```

Frontend will run on: `http://localhost:5173`

## Testing Flow

1. **Open Browser**: `http://localhost:5173`
2. **Ask a Question**: "Explain soil consolidation"
3. **Check Logs**:
   - Terminal 1 (Python): Should show multi-agent consensus running
   - Terminal 2 (TypeScript): Should show "[Brain] Using Python multi-agent brain system"

## What's Integrated?

✅ Python Brain (FastAPI on :8000) ← Multi-agent system
✅ TypeScript Backend (Express/tRPC on :3000) ← Calls Python Brain
✅ React Frontend (Vite on :5173) ← User interface

## Fallback Behavior

If Python Brain is down, the system automatically falls back to simple OpenAI LLM.

## Environment Variables

Make sure your `.env` has:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PYTHON_BRAIN_API_URL=http://localhost:8000
```

## Troubleshooting

**Problem**: Python Brain crashes
- **Solution**: Make sure all Python dependencies installed
- Check: `pip list | grep -E "(langchain|langgraph|faiss)"`

**Problem**: TypeScript can't reach Python
- **Solution**: Check Python Brain is running on port 8000
- Visit: `http://localhost:8000` (should show health check)

**Problem**: Frontend not loading
- **Solution**: Run `pnpm install` first
- Check: TypeScript backend is running

## Next Steps After Testing

1. ✅ Test locally (all 3 services)
2. 📝 Commit to Git
3. 🚀 Deploy (tomorrow)
