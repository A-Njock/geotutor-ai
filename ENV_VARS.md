# Environment Variables for Railway Deployment

## 🚂 TypeScript Backend Service

```env
NODE_ENV=production
PORT=3000
OPENAI_API_KEY=sk-yQZu4Td8aNFOYqV24aB8F729Cd394205B0C422Bc4456Ad46
PYTHON_BRAIN_API_URL=https://geotutor-brain.up.railway.app
```

*Note: Update `PYTHON_BRAIN_API_URL` after deploying the Python Brain service*

## 🐍 Python Brain Service

```env
PORT=8000
OPENAI_API_KEY=sk-yQZu4Td8aNFOYqV24aB8F729Cd394205B0C422Bc4456Ad46
```

## 🌐 Vercel Frontend

```env
VITE_API_URL=https://geotutor-backend.up.railway.app
```

*Note: Update with your actual Railway backend URL after deployment*

---

## 📋 Deployment Checklist

- [ ] Push code to GitHub: `git push -u origin main`
- [ ] Deploy Frontend to Vercel (root: `geotutor`)
- [ ] Deploy Backend to Railway (root: `geotutor`)
- [ ] Deploy Python Brain to Railway (root: `brain_api`)
- [ ] Update environment variables with actual URLs
- [ ] Test deployment

## 🔗 Your GitHub Repository

https://github.com/A-Njock/geotutor-ai
