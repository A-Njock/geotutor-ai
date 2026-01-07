# Quick Fix: Start GeoTutor

The backend isn't starting properly. Here's how to fix it:

## Problem
The `npm run dev` command uses Unix syntax that doesn't work on Windows PowerShell.

## Solution

### Option 1: Use cross-env (Recommended)

1. Install cross-env:
```bash
cd e:\YORK.A\Python codes2\Antigrav\geotutor
npm install --save-dev cross-env
```

2. Update package.json scripts:
Change:
```json
"dev": "NODE_ENV=development tsx watch server/_core/index.ts"
```

To:
```json
"dev": "cross-env NODE_ENV=development tsx watch server/_core/index.ts"
```

3. Run:
```bash
npm run dev
```

### Option 2: Manual PowerShell Command

Just run this directly in PowerShell:
```powershell
cd e:\YORK.A\Python codes2\Antigrav\geotutor
$env:NODE_ENV="development"; npx tsx watch server/_core/index.ts
```

### Option 3: Use CMD instead of PowerShell

```cmd
cd e:\YORK.A\Python codes2\Antigrav\geotutor
set NODE_ENV=development && npx tsx watch server/_core/index.ts
```

## What You Should See

After running, you should see:
```
Server running on http://localhost:3000/
```

Then open that URL in your browser!
