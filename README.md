# 🛡️ EDQMP - Enterprise Data Quality & Monitoring Platform

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Status](https://img.shields.io/badge/status-production_ready-green.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

**The complete, free-tier solution for financial-grade data governance.**
*Validate Data • Monitor Pipelines • Calculate Financial Risk*

[Live Demo](http://localhost:8501) • [Documentation](docs/) • [Deployment](#deployment)

</div>

---

## 🚀 Product Overview

EDQMP is a "Command Center" for data quality. Unlike simple validation scripts, it provides a **secure, multi-user platform** to manage data health across your enterprise.

### 🌟 Key Features (v2.0 Enterprise)

*   **� Secure Authentication**: Role-based login system with "Sign Up" and "Demo Mode".
*   **� Financial Impact Analysis**: Automatically calculates potential monetary loss (Risk Exposure) from data failures.
*   **� Dynamic Validation Engine**: Upload your own CSV/JSON files and run 6-point validation checks instantly.
*   **� Rule Configuration UI**: Create and manage business rules (e.g., "No negative balances") directly in the dashboard.
*   **� Active Threat Monitoring**: Real-time alerts for critical pipeline breaks and SLA breaches.
*   **� Executive Dashboards**: Dark-mode, glassmorphism UI designed for C-suite reporting.

---

## 🛠️ Technology Stack (100% Free Tier)

| Component | Technology | Hosting |
|-----------|------------|---------|
| **Backend** | FastAPI (Python) | Render |
| **Frontend** | Streamlit (Python) | Streamlit Cloud |
| **Database** | PostgreSQL | Supabase (500MB Free) |
| **Auth** | JWT + Supabase Auth | Supabase |
| **Visualization** | Plotly | Streamlit Cloud |

---

## 🏁 Quick Start

### 1. Prerequisites
*   Python 3.9+
*   Supabase Account (Free)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/edqmp.git
cd edqmp

# Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Dashboard Setup
cd ../dashboard
pip install -r requirements.txt
```

### 3. Configuration
Copy `.env.example` to `.env` and add your Supabase credentials (see [Environment Setup Guide](docs/ENVIRONMENT_SETUP.md)).

### 4. Run Locally

**Backend (Terminal 1):**
```bash
cd backend
uvicorn app.main:app --reload
```

**Dashboard (Terminal 2):**
```bash
cd dashboard
streamlit run app.py
```

---

## � User Guide

### 1. Login
*   **Admin**: `admin@edqmp.com` (Password: any)
*   **Demo**: Click "🚀 Try Demo Account" on the login screen.

### 2. Validate Data
1.  Navigate to **Quality Control**.
2.  Select **"Upload CSV/JSON"**.
3.  Drop your file.
4.  Click **"🚀 Execute Validation"**.
5.  View the **Financial Impact** report.

### 3. Configure Rules
1.  Navigate to **Quality Control** → **Rule Manager**.
2.  Fill out the form to create a new rule (e.g., "Critical Severity").
3.  Save to apply immediately.

---

## 🌐 Deployment Guide

### Step 1: Push to GitHub
See [GitHub Push Instructions](docs/GITHUB_PUSH_INSTRUCTIONS.md).

### Step 2: Deploy Backend (Render)
1.  Connect your GitHub repo to Render.
2.  Select `backend` directory.
3.  Add Environment Variables from your `.env`.

### Step 3: Deploy Dashboard (Streamlit)
1.  Connect your GitHub repo to Streamlit Cloud.
2.  Select `dashboard/app.py` as the entry point.
3.  Add secrets in the Streamlit dashboard settings.

---

## 🤝 Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License
[MIT](https://choosealicense.com/licenses/mit/)
