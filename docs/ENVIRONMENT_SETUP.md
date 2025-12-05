# EDQMP Environment Setup Guide

Complete guide for configuring environment variables and connecting to services.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Supabase Setup](#supabase-setup)
3. [Environment Variables Reference](#environment-variables-reference)
4. [Security Configuration](#security-configuration)
5. [Alerting Configuration](#alerting-configuration)
6. [Deployment Configuration](#deployment-configuration)

---

## 🚀 Quick Start

### Step 1: Create Environment File

```bash
# Navigate to backend directory
cd enterprise/backend

# Copy the example file
copy .env.example .env
```

### Step 2: Get Supabase Credentials

1. Go to [supabase.com](https://supabase.com) and sign up (FREE)
2. Create a new project
3. Wait for the database to be ready (~2 minutes)
4. Go to **Project Settings** → **API**
5. Copy the following values:

| Supabase Field | .env Variable |
|----------------|---------------|
| Project URL | `SUPABASE_URL` |
| anon/public key | `SUPABASE_KEY` |
| service_role key | `SUPABASE_SERVICE_KEY` |

### Step 3: Generate Secret Key

```powershell
# Generate a secure random key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste it as `SECRET_KEY` in your `.env` file.

### Step 4: Run Database Schema

1. In Supabase Dashboard, go to **SQL Editor**
2. Open `scripts/setup_supabase.sql` from this project
3. Copy the entire contents and paste into the SQL Editor
4. Click **Run** to create all tables, indexes, and policies

---

## 🗄️ Supabase Setup

### Creating Your Free Project

1. **Sign Up**: Visit [supabase.com](https://supabase.com) and create an account
2. **New Project**: Click "New Project" and fill in:
   - **Name**: `edqmp-production` (or any name)
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
3. **Wait**: Database provisioning takes ~2 minutes

### Finding Your API Keys

Navigate to **Project Settings** (gear icon) → **API**:

```
┌─────────────────────────────────────────────────────────────┐
│ Project Settings → API                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Project URL                                                  │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ https://xyzabc123.supabase.co                            ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ Project API keys                                             │
│                                                              │
│ anon / public                                                │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...                  ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ service_role (secret)                                        │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...                  ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Running the Database Schema

1. Go to **SQL Editor** in Supabase Dashboard
2. Click **+ New Query**
3. Copy contents from `scripts/setup_supabase.sql`
4. Click **Run** (or press Ctrl+Enter)
5. You should see "Success. No rows returned" for each statement

**Verify tables were created:**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```

Expected output:
- quality_rules
- data_sources
- rule_source_mappings
- validation_results
- pipeline_runs
- alert_configs
- alert_history
- audit_logs
- quality_metrics

---

## 📝 Environment Variables Reference

### Required Variables

```env
# ============================================
# SUPABASE CONFIGURATION (REQUIRED)
# ============================================

# Your Supabase project URL
# Format: https://[project-id].supabase.co
SUPABASE_URL=https://your-project-id.supabase.co

# Public/anon key for client-side operations
# Safe to expose in frontend (RLS enforced)
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Service role key for admin operations (KEEP SECRET!)
# Bypasses Row Level Security - use only in backend
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ============================================
# APPLICATION SECURITY (REQUIRED)
# ============================================

# Secret key for JWT token signing
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-super-secret-key-here

# ============================================
# APPLICATION SETTINGS
# ============================================

# Environment: development, staging, production
ENVIRONMENT=development

# Enable debug mode (set to false in production)
DEBUG=true

# Application name and version
APP_NAME=EDQMP
APP_VERSION=1.0.0
```

### Optional Variables

```env
# ============================================
# API CONFIGURATION
# ============================================

# API host and port
API_HOST=0.0.0.0
API_PORT=8000

# API prefix for all routes
API_PREFIX=/api/v1

# CORS allowed origins (comma-separated)
# Use * for development, specific domains for production
CORS_ORIGINS=http://localhost:8501,http://localhost:3000

# ============================================
# ALERTING - SLACK
# ============================================

# Slack webhook URL for sending alerts
# Get from: https://api.slack.com/messaging/webhooks
SLACK_WEBHOOK_URL=your-slack-webhook-url-here

# Default channel for alerts
SLACK_DEFAULT_CHANNEL=#data-quality-alerts

# ============================================
# ALERTING - EMAIL (SMTP)
# ============================================

# SMTP server configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourcompany.com

# ============================================
# ALERTING - SENDGRID (Alternative to SMTP)
# ============================================

# SendGrid API key
SENDGRID_API_KEY=SG.xxxxxxxxxxxx

# ============================================
# ALERTING - PAGERDUTY
# ============================================

# PagerDuty integration key
PAGERDUTY_INTEGRATION_KEY=your-pagerduty-key

# ============================================
# LOGGING
# ============================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log format: json, text
LOG_FORMAT=json
```

---

## 🔐 Security Configuration

### Generating a Secure Secret Key

**Option 1: Python**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Option 2: OpenSSL**
```bash
openssl rand -base64 32
```

**Option 3: PowerShell**
```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

### JWT Token Settings

```env
# Token expiration time (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Algorithm for JWT signing
JWT_ALGORITHM=HS256
```

### Important Security Notes

> ⚠️ **Never commit `.env` files to Git!**
> The `.gitignore` already excludes `.env` files.

> 🔒 **Keep `SUPABASE_SERVICE_KEY` secret!**
> This key bypasses Row Level Security. Only use in backend.

> 🔑 **Rotate `SECRET_KEY` periodically**
> Changing this will invalidate all existing JWT tokens.

---

## 🔔 Alerting Configuration

### Slack Integration

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create a new app → "From scratch"
3. Enable **Incoming Webhooks**
4. Add webhook to a channel
5. Copy the webhook URL to `SLACK_WEBHOOK_URL`

```env
SLACK_WEBHOOK_URL=your-slack-webhook-url-here
SLACK_DEFAULT_CHANNEL=#data-quality-alerts
```

### Email via Gmail (SMTP)

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Create a new app password for "Mail"

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

### SendGrid (Recommended for Production)

1. Create account at [sendgrid.com](https://sendgrid.com)
2. Create an API key with "Mail Send" permissions
3. Add to environment:

```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxx
SMTP_FROM=alerts@yourdomain.com
```

---

## 🚀 Deployment Configuration

### Render (Backend)

When deploying to Render, set these environment variables in the Render dashboard:

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | Your Supabase URL |
| `SUPABASE_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Your Supabase service key |
| `SECRET_KEY` | Generated secret key |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |

### Streamlit Cloud (Dashboard)

In Streamlit Cloud, go to **Settings** → **Secrets** and add:

```toml
[general]
API_URL = "https://your-render-app.onrender.com/api/v1"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
```

### Environment-Specific Files

For different environments, create separate files:

```
backend/
├── .env                 # Local development (gitignored)
├── .env.example         # Template (committed)
├── .env.staging         # Staging config (gitignored)
└── .env.production      # Production config (gitignored)
```

---

## ✅ Verification Checklist

After configuring your `.env` file, verify everything works:

- [ ] Backend starts without errors: `uvicorn app.main:app --reload`
- [ ] Health check returns OK: `curl http://localhost:8000/health`
- [ ] API docs load: Open http://localhost:8000/docs
- [ ] Database connection works: Test `/api/v1/quality/rules` endpoint
- [ ] Dashboard connects to API: Check sidebar status indicator

---

## 🆘 Troubleshooting

### "Invalid Supabase URL"
- Ensure URL starts with `https://`
- Check for trailing slashes (remove them)

### "Authentication failed"
- Verify `SUPABASE_KEY` is the anon/public key
- Check key wasn't accidentally truncated when copying

### "Database tables not found"
- Run `setup_supabase.sql` in Supabase SQL Editor
- Check you're connected to the correct project

### "CORS error in dashboard"
- Add dashboard URL to `CORS_ORIGINS`
- For development: `CORS_ORIGINS=*`

---

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
- [Streamlit Secrets Management](https://docs.streamlit.io/library/advanced-features/secrets-management)
- [Render Environment Variables](https://render.com/docs/environment-variables)
