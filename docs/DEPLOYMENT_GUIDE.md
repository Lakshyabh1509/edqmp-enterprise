# EDQMP Deployment Guide

Complete guide for deploying the Enterprise Data Quality & Monitoring Platform.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Supabase Setup](#supabase-setup)
3. [Vercel Deployment](#vercel-deployment)
4. [Netlify Deployment](#netlify-deployment)
5. [Local Development](#local-development)
6. [Environment Variables](#environment-variables)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- GitHub account with this repository
- [Supabase](https://supabase.com) account (free tier)
- [Vercel](https://vercel.com) or [Netlify](https://netlify.com) account (free tier)

### Deployment Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    VERCEL DEPLOYMENT                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   https://your-app.vercel.app/                             │
│   ├── /              → Frontend (HTML/CSS/JS)              │
│   ├── /api/v1/*      → Backend API (FastAPI)               │
│   ├── /docs          → API Documentation                   │
│   └── /health        → Health Check                        │
│                                                             │
│   Connected to:                                             │
│   └── Supabase (PostgreSQL + Auth)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

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

Navigate to **Project Settings** (gear icon) → **API**:

| Field | Use For |
|-------|---------|
| **Project URL** | `SUPABASE_URL` |
| **anon/public key** | `SUPABASE_KEY` |
| **service_role key** | `SUPABASE_SERVICE_KEY` (keep secret!) |

### Step 3: Enable Email Authentication

1. Go to **Authentication** → **Providers**
2. Click **Email**
3. Toggle **Enable Email Provider** = ON
4. Toggle **Confirm Email** = OFF (for easier testing)
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

## 🔷 Vercel Deployment

### Step 1: Import Repository

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New..."** → **"Project"**
3. Select **"Import Git Repository"**
4. Connect your GitHub account and select: `Lakshyabh1509/edqmp-enterprise`
5. Click **"Import"**

### Step 2: Configure Project

Leave these settings as default:
- **Framework Preset**: Other
- **Root Directory**: `.` (leave empty)
- **Build Command**: (leave empty)
- **Output Directory**: (leave empty)

### Step 3: Add Environment Variables

Click **"Environment Variables"** and add:

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | `https://rlvblrpfsfbnetdgnaqh.supabase.co` |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdmJscnBmc2ZibmV0ZGduYXFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ5Njc5MjYsImV4cCI6MjA4MDU0MzkyNn0.d4D5pTVgu9Jg36T2kXb3ZnC8OgcoPtzR_uqhme3qDHo` |
| `SECRET_KEY` | `Qx44eUKHB5rNhPzsexFNeQl1tR12c7yH5Y5v4EmvoaI` |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |

### Step 4: Deploy

Click **"Deploy"** and wait for the build to complete (~2-3 minutes).

### Step 5: Verify Deployment

After deployment, test these endpoints:

| Endpoint | Expected Result |
|----------|-----------------|
| `https://your-app.vercel.app/` | Frontend loads with login page |
| `https://your-app.vercel.app/health` | `{"status": "healthy"}` |
| `https://your-app.vercel.app/docs` | API documentation |

---

## 🌐 Netlify Deployment

### Step 1: Import Repository

1. Go to [netlify.com](https://netlify.com) and sign in
2. Click **"Add new site"** → **"Import an existing project"**
3. Connect GitHub and select: `Lakshyabh1509/edqmp-enterprise`

### Step 2: Configure Build Settings

| Setting | Value |
|---------|-------|
| **Base directory** | `frontend` |
| **Build command** | (leave empty) |
| **Publish directory** | `frontend` |

### Step 3: Add Environment Variables

Go to **Site settings** → **Environment Variables** and add:

```
SUPABASE_URL=https://rlvblrpfsfbnetdgnaqh.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

> ⚠️ **Note**: Netlify only hosts static sites. For the Python backend, you'll need to deploy separately on Vercel, Render, or Railway.

---

## 💻 Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+ (optional, for dev tools)

### Step 1: Clone Repository

```bash
git clone https://github.com/Lakshyabh1509/edqmp-enterprise.git
cd edqmp-enterprise
```

### Step 2: Create Environment File

```bash
# Copy example to .env
copy .env.example .env

# Edit with your Supabase credentials
notepad .env
```

**.env contents:**
```env
SUPABASE_URL=https://rlvblrpfsfbnetdgnaqh.supabase.co
SUPABASE_KEY=your-anon-key
SECRET_KEY=your-secret-key
ENVIRONMENT=development
DEBUG=true
```

### Step 3: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Run Backend

```bash
# From backend directory
uvicorn app.main:app --reload --port 8000
```

Backend will be at: http://localhost:8000

### Step 5: Run Frontend

```bash
# From frontend directory
cd ../frontend
python -m http.server 3000
```

Frontend will be at: http://localhost:3000

### Step 6: Test the App

1. Open http://localhost:3000
2. Click **"Try Demo Account"** or sign up
3. Explore the dashboard!

---

## 🔧 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Your Supabase project URL | `https://xyz.supabase.co` |
| `SUPABASE_KEY` | Supabase anon/public key | `eyJhbGciOiJI...` |
| `SECRET_KEY` | JWT signing key (32+ chars) | `Qx44eUKHB5rN...` |
| `ENVIRONMENT` | `development` or `production` | `production` |
| `DEBUG` | Enable debug mode | `false` |

### Generate SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Current Configuration (Your Project)

```env
SUPABASE_URL=https://rlvblrpfsfbnetdgnaqh.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsdmJscnBmc2ZibmV0ZGduYXFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ5Njc5MjYsImV4cCI6MjA4MDU0MzkyNn0.d4D5pTVgu9Jg36T2kXb3ZnC8OgcoPtzR_uqhme3qDHo
SECRET_KEY=Qx44eUKHB5rNhPzsexFNeQl1tR12c7yH5Y5v4EmvoaI
ENVIRONMENT=production
DEBUG=false
```

---

## 🔐 Security Best Practices

### Never Commit Secrets

The `.gitignore` is configured to exclude:
- `.env` files
- `secrets/` directories
- `*.pem` and `*.key` files

### Rotate SECRET_KEY Periodically

When you change SECRET_KEY:
- All existing JWT tokens become invalid
- Users will need to log in again

### Use HTTPS Only

Vercel and Netlify provide free SSL certificates automatically.

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'scipy'"

**Solution**: The code has been updated to make scipy optional. Redeploy.

### "Supabase connection failed"

**Check**:
- URL doesn't have trailing slash
- API key wasn't truncated when copying
- Project is not paused (free tier pauses after inactivity)

### "Application Error" on Vercel

**Check**:
1. View deployment logs in Vercel dashboard
2. Verify all environment variables are set
3. Try clearing build cache: **Settings** → **General** → **Clear Build Cache**

### Frontend shows blank page

**Check**:
- Browser console for JavaScript errors
- Network tab for failed API requests
- API endpoint is accessible

### Login not working

**Check**:
1. Supabase Email provider is enabled
2. Supabase project is not paused
3. API is returning proper responses

---

## 📚 Project Structure

```
edqmp-enterprise/
├── frontend/               # Static web frontend
│   ├── index.html         # Main HTML page
│   ├── styles.css         # Premium dark theme
│   └── app.js             # Application logic
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── main.py       # Entry point
│   │   ├── api/          # API routes
│   │   ├── core/         # Database, auth
│   │   ├── engines/      # Validation engines
│   │   └── schemas/      # Pydantic models
│   └── requirements.txt
├── dashboard/             # Streamlit dashboard (legacy)
├── docs/                  # Documentation
├── scripts/               # Database setup scripts
├── vercel.json           # Vercel configuration
└── .env.example          # Environment template
```

---

## 🔗 Useful Links

| Resource | URL |
|----------|-----|
| **Live App** | https://edqmp-enterprise.vercel.app |
| **GitHub Repo** | https://github.com/Lakshyabh1509/edqmp-enterprise |
| **Supabase Dashboard** | https://app.supabase.com |
| **Vercel Dashboard** | https://vercel.com/dashboard |

---

## ✅ Deployment Checklist

- [ ] Supabase project created
- [ ] Database schema executed
- [ ] Email auth enabled in Supabase
- [ ] Repository pushed to GitHub
- [ ] Vercel project created
- [ ] Environment variables configured
- [ ] Deployment successful
- [ ] Health endpoint returns OK
- [ ] Frontend loads correctly
- [ ] Login/Demo mode works
- [ ] API documentation accessible

---

*Last updated: December 2024*
