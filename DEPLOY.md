# Deploying GeoTutor (GitHub + Railway)

Two services, one repository:

| Service | Root | Runs |
|---|---|---|
| geotutor-brain | repo root, `brain_api/Dockerfile` | FastAPI Python brain (Modes 1 + 2) |
| geotutor-web | `geotutor/` | Node web app (Vite client + tRPC server) |

The repository ships the STRICT MINIMUM: application code only. Not in the
repo (by design): the PDF library (copyrighted), the 2.7 GB Mode 1 index
(`data/`), the benchmark vendor clone, virtualenvs, node_modules, real keys.

## 0. Before anything

- Rotate every API key that ever appeared in this repo's history; treat old
  ones as compromised. Put real values ONLY in Railway variables / local `.env`.
- Local smoke test first (localhost rule): backend
  `uvicorn brain_api.main:api` on :8000, frontend `pnpm dev` in `geotutor/`,
  solve one Design problem and ask one Chat question.

## 1. GitHub

A clean single-commit history (old history contains leaked keys and belongs
to the previous repository):

```
git checkout --orphan release
git add -A         # .gitignore already excludes everything private/heavy
git commit -m "GeoTutor: clean deployment snapshot"
git push <remote> release:main --force     # to a NEW private repo
```

## 2. Railway: geotutor-brain (Python)

1. New service from the GitHub repo. Builder: Dockerfile,
   path `brain_api/Dockerfile` (build context = repo root).
2. Variables: `DEEPSEEK_API_KEY` (required), `DATA_DIR=/app/data`,
   optionally `INDEX_ARCHIVE_URL` (see step 4).
3. Attach a volume mounted at `/app/data` (>= 5 GB) for the Mode 1 index.
4. Mode 1 index (2.7 GB, not in git). Two options:
   - `tar czf index.tar.gz -C data .` locally, upload the archive to any
     private URL you control, set `INDEX_ARCHIVE_URL`; the entrypoint
     downloads and unpacks it into the volume on first boot, then never again.
   - Or leave it unset: Design mode works fully; Chat mode answers with the
     maintenance message until the index is present.
5. Note the public URL (e.g. `https://geotutor-brain.up.railway.app`).

## 3. Railway: geotutor-web (Node)

1. New service from the same repo, root directory `geotutor` (Nixpacks
   detects pnpm; build `pnpm build`, start `pnpm start`).
2. Variables:
   - `NODE_ENV=production`
   - `VITE_PYTHON_BRAIN_API_URL=<brain public URL>`  (build-time: set BEFORE
     the first build; rebuild after changing it)
   - leave DB/OAuth variables empty to run exactly like local guest mode.

## 4. After deploy

- Open the web URL, use "Continue as Guest", solve one problem from each
  family chip sentence (Design) and ask one Chat question.
- Confirm the maintenance card appears if you temporarily remove
  `DEEPSEEK_API_KEY` (optional check).

## Cost/size notes

- The brain image is large (torch via sentence-transformers). If image size
  becomes a problem, Chat mode's embedding model can be swapped to an API
  later; Design mode alone needs none of it.
- Railway free/hobby limits: keep one replica; the index volume is the main
  storage consumer.
