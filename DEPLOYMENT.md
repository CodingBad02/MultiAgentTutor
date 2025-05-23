# 🚀 Deployment Guide - Multi-Agent AI Tutor

This guide covers deployment to Railway (recommended) and Vercel.

## 📋 Prerequisites

1. **Gemini API Key**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, etc.)

## 🛤️ Option 1: Railway (Recommended)

Railway is perfect for FastAPI applications with persistent connections and external APIs.

### Step 1: Prepare Your Repository

Ensure these files are in your repository root:
- ✅ `requirements.txt` (dependencies)
- ✅ `railway.toml` (Railway configuration)
- ✅ `Procfile` (process definition)

### Step 2: Deploy to Railway

1. **Sign up/Login**: Go to [railway.app](https://railway.app) and sign up with GitHub
2. **Create New Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select Repository**: Choose your multi-agent tutor repository
4. **Set Environment Variables**:
   ```
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ENVIRONMENT=production
   PORT=8000
   ```

### Step 3: Configure Domain (Optional)

1. Go to your Railway project dashboard
2. Click "Settings" → "Domain"
3. Generate a Railway domain or add a custom domain

### Step 4: Test Deployment

Visit your Railway URL and test:
- `GET /` - Should return system info
- `GET /health` - Should return health status
- `POST /ask` - Test with a query like "Solve 2x + 5 = 15"

## 🔺 Option 2: Vercel (Alternative)

Vercel works but has limitations for persistent services.

### Step 1: Prepare for Vercel

Ensure these files exist:
- ✅ `vercel.json` (Vercel configuration)
- ✅ `api/index.py` (Vercel API handler)
- ✅ `requirements.txt` (dependencies)

### Step 2: Deploy to Vercel

1. **Install Vercel CLI**: `npm i -g vercel`
2. **Login**: `vercel login`
3. **Deploy**: `vercel --prod`
4. **Set Environment Variables**:
   ```bash
   vercel env add GEMINI_API_KEY
   vercel env add ENVIRONMENT production
   ```

### Step 3: Test Deployment

Visit your Vercel URL and test the endpoints.

## 🔧 Environment Variables

Both platforms need these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Your Google Gemini API key | `AIza...` |
| `ENVIRONMENT` | Deployment environment | `production` |
| `PORT` | Server port (Railway only) | `8000` |

## 🧪 Testing Your Deployment

### Health Check
```bash
curl https://your-app-url.railway.app/health
```

### Solve an Equation
```bash
curl -X POST "https://your-app-url.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "Solve 2x + 5 = 15"}'
```

### Get a Formula
```bash
curl -X POST "https://your-app-url.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the formula for kinetic energy?"}'
```

## 🔍 Debugging Deployment Issues

### Railway
- Check logs: Railway dashboard → "Deployments" → "View Logs"
- Common issues: Missing environment variables, port configuration

### Vercel
- Check function logs: Vercel dashboard → "Functions" → "View Function"
- Common issues: Cold starts, timeout limits (10s max)

## 🌟 Deployment Comparison

| Feature | Railway | Vercel |
|---------|---------|--------|
| **Setup Complexity** | Easy | Moderate |
| **Cold Starts** | Minimal | Yes (slower) |
| **Persistent State** | Yes | No |
| **Timeout Limits** | None | 10 seconds |
| **Cost (Free Tier)** | $5/month after trial | Free (with limits) |
| **Best For** | Full applications | Serverless functions |

## 🎯 Recommendation

**Use Railway** for this multi-agent system because:
- ✅ Better suited for FastAPI applications
- ✅ No serverless timeout limits
- ✅ Easier environment variable management
- ✅ Better logging and debugging
- ✅ Persistent connections work better

## 🚨 Security Notes

For production deployment:
1. **Restrict CORS origins** in `app/main.py`
2. **Add API rate limiting**
3. **Use HTTPS only**
4. **Monitor API usage and costs**
5. **Keep your Gemini API key secure**

## 🆘 Getting Help

If deployment fails:
1. Check the platform-specific logs
2. Verify all environment variables are set
3. Test locally first: `uvicorn app.main:app --reload`
4. Check Railway/Vercel documentation for platform-specific issues 