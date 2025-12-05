# 🐙 How to Push EDQMP to GitHub

Follow these exact steps to push your code to a new GitHub repository.

---

## Step 1: Create a Repository on GitHub

1.  Log in to [GitHub.com](https://github.com).
2.  Click the **+** icon in the top-right corner and select **New repository**.
3.  **Repository name**: `edqmp-enterprise` (or any name you prefer).
4.  **Description**: "Enterprise Data Quality & Monitoring Platform".
5.  **Public/Private**: Choose **Public** (easier for deployment) or **Private**.
6.  **Initialize**: Do **NOT** check "Add a README", ".gitignore", or "license". We already have these.
7.  Click **Create repository**.

---

## Step 2: Initialize Git Locally

Open your terminal (PowerShell or Command Prompt) in the project folder:

```powershell
cd c:\Users\Lakshya\Downloads\final\enterprise
```

Run these commands one by one:

```bash
# 1. Initialize a new Git repository
git init

# 2. Add all files to staging
git add .

# 3. Commit the files
git commit -m "Initial commit: EDQMP Enterprise v2.0"

# 4. Rename branch to main (best practice)
git branch -M main
```

---

## Step 3: Connect and Push

Replace `YOUR_USERNAME` with your actual GitHub username in the command below.

```bash
# 5. Add the remote origin (LINK TO YOUR REPO)
git remote add origin https://github.com/YOUR_USERNAME/edqmp-enterprise.git

# 6. Push the code
git push -u origin main
```

> **Note**: If asked for a password, use your **GitHub Personal Access Token**, not your account password.

---

## Step 4: Verify

1.  Refresh your GitHub repository page.
2.  You should see all your files (`backend`, `dashboard`, `README.md`, etc.).
3.  You are now ready to deploy to Render and Streamlit Cloud!
