# Mindrian Deployment Guide

This guide walks you through deploying Mindrian to the cloud using **free tiers**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MINDRIAN CLOUD ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐         ┌─────────────┐                        │
│  │   Vercel    │ ──────> │   Render    │                        │
│  │  (Frontend) │   API   │  (Backend)  │                        │
│  │    FREE     │         │    FREE     │                        │
│  └─────────────┘         └──────┬──────┘                        │
│                                 │                                │
│                    ┌────────────┼────────────┐                  │
│                    │            │            │                  │
│              ┌─────▼─────┐ ┌────▼────┐ ┌────▼────┐             │
│              │  Neo4j    │ │Pinecone │ │Anthropic│             │
│              │  Aura     │ │         │ │  API    │             │
│              │  FREE     │ │  FREE   │ │  PAY    │             │
│              └───────────┘ └─────────┘ └─────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

You'll need accounts on:
- [GitHub](https://github.com) (already have)
- [Render](https://render.com) - Backend hosting
- [Vercel](https://vercel.com) - Frontend hosting
- [Neo4j Aura](https://neo4j.com/cloud/aura/) - Graph database (already have)
- [Pinecone](https://pinecone.io) - Vector database (already have)
- [Anthropic](https://anthropic.com) - Claude API

## Step 1: Deploy Backend to Render

### 1.1 Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub (recommended - auto-connects repos)

### 1.2 Deploy the Backend

**Option A: Using the Render Dashboard**

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repo: `jsagir/mindrian-agno-V1-171225`
3. Configure:
   - **Name**: `mindrian-api`
   - **Region**: Oregon (US West) - required for free tier
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -e .`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

4. Add Environment Variables (in Render dashboard):
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   PINECONE_API_KEY=your-key
   PINECONE_INDEX=mindrian
   ENVIRONMENT=production
   ```

5. Click **"Create Web Service"**

**Option B: Using render.yaml (Blueprint)**

1. The repo already has `render.yaml`
2. In Render dashboard, click **"New +"** → **"Blueprint"**
3. Connect the repo
4. Render will auto-detect the blueprint
5. Add the secret environment variables

### 1.3 Verify Deployment

Once deployed, you'll get a URL like:
```
https://mindrian-api.onrender.com
```

Test it:
```bash
curl https://mindrian-api.onrender.com/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

## Step 2: Deploy Frontend to Vercel

### 2.1 Fork Agno Agent UI

1. Go to [github.com/agno-agi/agent-ui](https://github.com/agno-agi/agent-ui)
2. Click **"Fork"** to your account
3. Name it: `mindrian-ui`

### 2.2 Configure for Mindrian

Clone your fork locally:
```bash
git clone https://github.com/jsagir/mindrian-ui.git
cd mindrian-ui
```

Update `.env.local`:
```env
NEXT_PUBLIC_API_URL=https://mindrian-api.onrender.com
```

Push changes:
```bash
git add .
git commit -m "Configure for Mindrian backend"
git push
```

### 2.3 Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Click **"Import Project"**
4. Select your `mindrian-ui` fork
5. Configure:
   - **Framework**: Next.js (auto-detected)
   - **Root Directory**: `.` (or `cookbook/playground` if using that structure)

6. Add Environment Variable:
   ```
   NEXT_PUBLIC_API_URL=https://mindrian-api.onrender.com
   ```

7. Click **"Deploy"**

You'll get a URL like:
```
https://mindrian-ui.vercel.app
```

## Step 3: Connect Frontend to Backend

### Update CORS (if needed)

If you get CORS errors, update the backend's allowed origins:

In `api/main.py`, the CORS is configured to allow all origins for now. For production, update:

```python
origins = [
    "https://mindrian-ui.vercel.app",
    "https://your-custom-domain.com",
]
```

Then redeploy.

## Environment Variables Reference

### Backend (Render)

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key from Anthropic | Yes |
| `NEO4J_URI` | Neo4j Aura connection URI | Yes |
| `NEO4J_USER` | Neo4j username (usually `neo4j`) | Yes |
| `NEO4J_PASSWORD` | Neo4j password | Yes |
| `PINECONE_API_KEY` | Pinecone API key | Yes |
| `PINECONE_INDEX` | Pinecone index name | Yes |
| `ENVIRONMENT` | `production` or `development` | No |
| `FRONTEND_URL` | Your Vercel URL (for CORS) | No |

### Frontend (Vercel)

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Your Render backend URL | Yes |

## Troubleshooting

### Backend won't start

1. Check Render logs for errors
2. Verify all environment variables are set
3. Test locally first: `uvicorn api.main:app --reload`

### "Service Unavailable" on Render free tier

Free tier services "spin down" after 15 minutes of inactivity. First request after spin-down takes ~30 seconds. This is normal.

### CORS errors in browser

1. Check that `FRONTEND_URL` is set in Render
2. Verify the URL matches exactly (including `https://`)
3. Clear browser cache

### Neo4j connection failed

1. Verify your Neo4j Aura instance is running
2. Check the URI format: `neo4j+s://xxxxx.databases.neo4j.io`
3. Test connection: `cypher-shell -a <URI> -u neo4j -p <password>`

### Pinecone errors

1. Verify index exists and matches `PINECONE_INDEX`
2. Check API key is correct
3. Ensure index region matches (some operations are region-specific)

## Custom Domain (Optional)

### For Frontend (Vercel)
1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records as instructed

### For Backend (Render)
1. Go to Service Settings → Custom Domain
2. Add your domain
3. Update DNS records as instructed

## Monitoring

### Render
- View logs: Dashboard → Service → Logs
- View metrics: Dashboard → Service → Metrics

### Vercel
- View logs: Dashboard → Project → Logs
- View analytics: Dashboard → Project → Analytics

## Cost Summary

| Service | Plan | Cost |
|---------|------|------|
| Render (Backend) | Free | $0/month |
| Vercel (Frontend) | Hobby | $0/month |
| Neo4j Aura | Free | $0/month |
| Pinecone | Starter | $0/month |
| Anthropic Claude | Pay-as-you-go | ~$5-20/month (usage dependent) |

**Total: ~$5-20/month** (only Anthropic API has costs)

## Next Steps

After deployment:

1. **Test the API**: Visit `https://your-api.onrender.com/docs` for Swagger UI
2. **Test the Frontend**: Visit `https://your-app.vercel.app`
3. **Share with testers**: Send them the Vercel URL
4. **Monitor usage**: Watch Anthropic API costs
5. **Iterate**: Make changes, push to GitHub, auto-deploys happen
