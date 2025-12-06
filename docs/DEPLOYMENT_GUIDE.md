# EDQMP Deployment Guide

Complete guide for deploying the Enterprise Data Quality & Monitoring Platform to production.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Supabase Setup](#supabase-setup)
4. [Backend Deployment (Render)](#backend-deployment-render)
5. [Dashboard Deployment (Streamlit Cloud)](#dashboard-deployment-streamlit-cloud)
6. [Alternative: Vercel Deployment](#alternative-vercel-deployment)
7. [Environment Variables Reference](#environment-variables-reference)
8. [Post-Deployment Verification](#post-deployment-verification)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION SETUP                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────┐      ┌─────────────────┐                     │
│   │  Streamlit      │      │  FastAPI        │                     │
│   │  Dashboard      │ ───► │  Backend        │                     │
│   │  (Frontend)     │      │  (API)          │                     │
│   └────────┬────────┘      └────────┬────────┘                     │
│            │                        │                              │
│            │    Streamlit Cloud     │    Render.com                │
│            │    or Vercel           │    or Railway                │
│            │                        │                              │
│            └────────────┬───────────┘                              │
│                         │                                          │
│                         ▼                                          │
│              ┌─────────────────────┐                               │
│              │     Supabase        │                               │
│              │   (PostgreSQL +     │                               │
│              │    Auth + API)      │                               │
│              └─────────────────────┘                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✅ Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] **Supabase Project** created at [supabase.com](https://supabase.com)
- [ ] **Database Schema** executed via SQL Editor
- [ ] **GitHub Repository** with your code pushed
- [ ] **Render Account** at [render.com](https://render.com) (free tier available)
- [ ] **Streamlit Cloud Account** at [streamlit.io/cloud](https://streamlit.io/cloud) (free tier available)

---

## 🗄️ Supabase Setup

### Step 1: Create Project

1. Go to [supabase.com](https://supabase.com) and sign up (FREE)
2. Click **"New Project"**
3. Fill in:
   - **Name**: `edqmp-production`
   - **Database Password**: Generate a strong password (SAVE THIS!)
   - **Region**: Choose closest to your users
4. Wait ~2 minutes for provisioning

### Step 2: Get API Keys

Navigate to **Project Settings** → **API**:

| Field | Use For |
|-------|---------|
| Project URL | `SUPABASE_URL` |
| anon/public key | `SUPABASE_KEY` |
| service_role key | `SUPABASE_SERVICE_KEY` (keep secret!) |

### Step 3: Enable Email Authentication

1. Go to **Authentication** → **Providers**
2. Click **Email**
3. Enable the toggle
4. Set **Confirm Email** = OFF (for easier testing)
5. Click **Save**

### Step 4: Run Database Schema

1. Go to **SQL Editor** → **New Query**
2. Copy contents from `scripts/setup_supabase.sql`
3. Click **Run**

**Verify tables created:**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```

Expected tables:
- `quality_rules`
- `data_sources`
- `rule_source_mappings`
- `validation_results`
- `pipeline_runs`
- `alert_configs`
- `alert_history`
- `audit_logs`
- `quality_metrics`

---

## 🚀 Backend Deployment (Render)

### Step 1: Prepare Local Files

Ensure these files exist in `backend/`:

**`requirements.txt`** - Already exists ✅

**`Procfile`** (create if missing):
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 2: Deploy to Render

1. Go to [render.com](https://render.com) and sign up
2. Click **"New +"** → **"Web Service"**
3. Connect your **GitHub repository**
4. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `edqmp-api` |
| **Region** | Closest to users |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

5. Add **Environment Variables**:

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | `https://rlvblrpfsfbnetdgnaqh.supabase.co` |
| `SUPABASE_KEY` | Your anon key |
| `SUPABASE_SERVICE_KEY` | Your service_role key |
| `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `PYTHON_VERSION` | `3.11.0` |

6. Click **"Create Web Service"**

### Step 3: Verify Backend

Once deployed, test:
- Health check: `https://your-app.onrender.com/health`
- API docs: `https://your-app.onrender.com/docs`

---

## 📊 Dashboard Deployment (Streamlit Cloud)

### Step 1: Prepare Configuration

Create `dashboard/.streamlit/secrets.toml`:

```toml
[general]
API_URL = "https://your-render-app.onrender.com/api/v1"

[supabase]
url = "https://rlvblrpfsfbnetdgnaqh.supabase.co"
key = "your-anon-key"
```

> ⚠️ **Don't commit this file!** Add to `.gitignore`

### Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Connect your **GitHub repository**
4. Configure:

| Setting | Value |
|---------|-------|
| **Repository** | Your repo |
| **Branch** | `main` |
| **Main file path** | `dashboard/app.py` |

5. In **Advanced settings** → **Secrets**, paste:

```toml
[general]
API_URL = "https://your-render-app.onrender.com/api/v1"

[supabase]
url = "https://rlvblrpfsfbnetdgnaqh.supabase.co"
key = "your-anon-key"
```

6. Click **"Deploy!"**

---

## 🔄 Alternative: Vercel Deployment

> ⚠️ **Note**: Vercel is optimized for JavaScript/Next.js. For Python apps like this, Render is recommended. However, you CAN deploy the FastAPI backend using Vercel's serverless functions.

### Backend on Vercel (Advanced)

1. Create `backend/vercel.json`:

```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

2. Deploy via Vercel CLI:
```bash
cd backend
vercel --prod
```

3. Set environment variables in Vercel Dashboard → Settings → Environment Variables

### Dashboard Alternative: Railway

Railway is another excellent option that supports Python natively:

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select your repository
4. Railway auto-detects Python and deploys

---

## 📝 Environment Variables Reference

### Backend (Production)

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_KEY` | Supabase anon/public key | ✅ |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | ✅ |
| `SECRET_KEY` | JWT signing key (32+ chars) | ✅ |
| `ENVIRONMENT` | `production` | ✅ |
| `DEBUG` | `false` | ✅ |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | ⚪ |
| `LOG_LEVEL` | `INFO` or `WARNING` | ⚪ |

### Dashboard (Streamlit Secrets)

```toml
[general]
API_URL = "https://your-api.onrender.com/api/v1"

[supabase]
url = "https://your-project.supabase.co"
key = "your-anon-key"
```

---

## 🔐 Security Best Practices

### Generate Secure SECRET_KEY

```python
# Run this locally to generate a secure key
import secrets
print(secrets.token_urlsafe(32))
```

Example output: `kJ8xNw3RbVfY2LmPqS4TuZ9AcE1DgH5IoK6MnQrW`

### What SECRET_KEY Does

| Purpose | Description |
|---------|-------------|
| **JWT Signing** | Signs authentication tokens so they can't be forged |
| **Session Security** | Encrypts session data |
| **Token Validation** | Verifies tokens haven't been tampered with |

> ⚠️ **Never share your SECRET_KEY!** If compromised, regenerate immediately.

### Rotating SECRET_KEY

When you change the SECRET_KEY:
- All existing JWT tokens become invalid
- Users will need to log in again
- This is a security feature, not a bug

---

## ✅ Post-Deployment Verification

### Backend Checks

```bash
# Health check
curl https://your-app.onrender.com/health

# Expected response:
# {"status": "healthy", "version": "1.0.0"}
```

### Dashboard Checks

1. Open your Streamlit URL
2. Verify sidebar shows "API Connected" status
3. Test login/signup flow
4. Verify data loads correctly

### Full Integration Test

1. Create a quality rule in the dashboard
2. Run a validation
3. Check results appear
4. Verify alerts are triggered (if configured)

---

## 🆘 Troubleshooting

### "Application Error" on Render

- Check **Logs** in Render dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` has all dependencies

### "Supabase connection failed"

- Verify URL doesn't have trailing slash
- Check API key wasn't truncated when copying
- Ensure RLS policies are correctly set up

### Dashboard can't reach API

- Verify `API_URL` in secrets is correct
- Check CORS_ORIGINS includes Streamlit domain
- Test API endpoint directly in browser

---

## 📚 Quick Reference

### Deployment URLs (After Setup)

| Service | URL |
|---------|-----|
| Backend API | `https://edqmp-api.onrender.com` |
| API Docs | `https://edqmp-api.onrender.com/docs` |
| Dashboard | `https://your-app.streamlit.app` |
| Supabase | `https://rlvblrpfsfbnetdgnaqh.supabase.co` |

### Useful Commands

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Test API locally
curl http://localhost:8000/health

# Run backend locally
cd backend && uvicorn app.main:app --reload

# Run dashboard locally
cd dashboard && streamlit run app.py
```

---

## 🎯 Recommended Hosting Stack

| Component | Free Tier | Recommendation |
|-----------|-----------|----------------|
| **Backend** | Render (750 hrs/month) | ⭐ Best for Python |
| **Dashboard** | Streamlit Cloud (unlimited) | ⭐ Best for Streamlit |
| **Database** | Supabase (500MB, 50K requests) | ⭐ Best for PostgreSQL |
| **Alternative** | Railway ($5 credit/month) | Good all-in-one |

---

*Last updated: December 2024*
