# Environment Variables for Deployment

Never put real key values in this file or anywhere else in the repository.
Real values live only in the local `.env` (gitignored) and in the Railway
service variables.

## Python Brain service (brain_api)

```env
PORT=8000
DEEPSEEK_API_KEY=<set in Railway variables>
# Optional, only if the multi-model council / figure generation is used:
OPENAI_API_KEY=<set in Railway variables>
MISTRAL_API_KEY=<set in Railway variables>
GEMINI_API_KEY=<set in Railway variables>
# Optional: URL of a tar.gz with the Mode 1 library index, downloaded on
# first boot into the mounted volume (see DEPLOY.md)
INDEX_ARCHIVE_URL=<optional>
# Feedback reports (thumbs-down batches emailed to the maintainer).
# Without RESEND_API_KEY the ratings still accumulate on the volume and
# the email is sent once the key is added.
RESEND_API_KEY=<optional, from resend.com>
FEEDBACK_EMAIL_TO=<optional, defaults to the maintainer address>
FEEDBACK_BATCH_SIZE=<optional, defaults to 10>
```

## Web app service (geotutor)

```env
NODE_ENV=production
PORT=3000
VITE_PYTHON_BRAIN_API_URL=<public URL of the brain service>
```

## Notes

- All keys that ever appeared in this repository's history are treated as
  compromised: rotate them with the provider before deploying.
- See DEPLOY.md for the full step-by-step deployment procedure.
