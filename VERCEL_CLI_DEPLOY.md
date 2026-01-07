# Vercel CLI Deployment

Install Vercel CLI and deploy directly from command line:

```bash
# Install Vercel CLI globally
npm install -g vercel

# Login to Vercel
vercel login

# Deploy from geotutor directory
cd geotutor
vercel --prod

# When prompted:
# - Set up and deploy? YES
# - Which scope? (select your account)
# - Link to existing project? YES
# - What's your project's name? geotutor-ai
# - In which directory is your code? ./
# - Override settings? NO (it will auto-detect)
```

This will deploy correctly without fighting with the UI!
