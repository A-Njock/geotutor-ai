# Deployment Guide - GeoTutor Full Stack

## 🎯 Architecture Overview

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  React Frontend │─────▶│ TypeScript API   │─────▶│  Python Brain   │
│   (Vercel)      │      │  (Railway)       │      │  (Railway/HF)   │
│  Port: 443      │      │  Port: 3000      │      │  Port: 8000     │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

## 📦 **Step 1: Prepare Repository**

### Create `.gitignore` (if not exists)
Already exists, verify it includes:
- `node_modules/`
- `.env`
- `dist/`  
- `__pycache__/`
- `*.pyc`

### Commit Everything
```bash
cd e:\YORK.A\Python codes2\Antigrav
git add .
git commit -m "feat: complete Python brain integration with GeoTutor

- FastAPI wrapper for multi-agent system
- TypeScript backend with intelligent fallback
- Enhanced pedagogical visual prompts
- Student/Teacher mode UI with access code
- All syntax issues resolved"

git push origin main
```

## 🚀 **Step 2: Deploy Frontend (Vercel)**

### 2.1 Connect to GitHub
1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "Add New" → "Project"
4. Select your `Antigrav` repository
5. Set **Root Directory**: `geotutor`

### 2.2 Configure Build Settings
```
Framework Preset: Vite
Build Command: pnpm build
Output Directory: dist/public
Install Command: pnpm install
```

### 2.3 Environment Variables
```
VITE_API_URL=https://your-backend.railway.app
```

### 2.4 Deploy
- Click "Deploy"
- Wait 2-3 minutes
- Get your URL: `https://geotutor-xxx.vercel.app`

## 🚂 **Step 3: Deploy TypeScript Backend (Railway)**

### 3.1 Create New Project
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Set **Root Directory**: `geotutor`

### 3.2 Configure Service
```
Start Command: npm start
Build Command: npm run build
```

### 3.3 Environment Variables
```
NODE_ENV=production
PORT=3000
OPENAI_API_KEY=your_key_here
PYTHON_BRAIN_API_URL=https://your-python-brain.railway.app
DATABASE_URL=postgresql://... (Railway will provide)
OAUTH_SERVER_URL=your_oauth_url (if needed)
```

### 3.4 Generate Domain
- Railway auto-generates: `your-backend.railway.app`
- Copy this URL for frontend env var

## 🐍 **Step 4: Deploy Python Brain (Railway)**

### 4.1 Create requirements.txt for Brain
Already created at `brain_api/requirements.txt`

### 4.2 Create Procfile
```
web: cd brain_api && uvicorn main:api --host 0.0.0.0 --port $PORT
```

### 4.3 Deploy to Railway
1. New Project → "Deploy from GitHub repo"
2. Set **Root Directory**: `brain_api`
3. Railway detects Python automatically

### 4.4 Environment Variables
```
PORT=8000
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### 4.5 Get Domain
- Copy generated URL for TypeScript backend

## 🔗 **Step 5: Connect Everything**

### Update Frontend .env
```env
VITE_API_URL=https://geotutor-backend.railway.app
```

### Update TypeScript Backend .env  
```env
PYTHON_BRAIN_API_URL=https://geotutor-brain.railway.app
```

### Redeploy
- Vercel: Auto-redeploys on git push
- Railway: Auto-redeploys on git push

## ✅ **Step 6: Test Deployment**

1. Visit `https://geotutor-xxx.vercel.app`
2. Ask a question
3. Check Railway logs to see:
   - TypeScript backend receiving request
   - Calling Python Brain
   - Returning answer

## 💰 **Cost Estimate**

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Hobby | **Free** |
| Railway (TypeScript) | Start | **$5/month** |
| Railway (Python Brain) | Start | **$5/month** |
| **Total** | | **~$10/month** |

## 🔄 **Alternative: Single Railway Deployment**

Deploy all in one Railway project (monorepo):
- Frontend: Static files served by TypeScript backend
- Backend: Express + tRPC
- Python Brain: Separate service in same project

**Cost**: $5-10/month total

## 📊 **What You'll Need**

1. ✅ GitHub account
2. ✅ Vercel account (free)
3. ✅ Railway account ($5 credit free)
4. ✅ OpenAI API key
5. ✅ Anthropic API key (optional)

Ready to deploy? I'll guide you through each step!
