# InnaIT IAM Audit Platform

**Production IAM Security Audit Tool — 11 modules, 100 questions**
Built for Precision Group · InnaIT Identity Security

---

## Run Locally

**Windows** -- double-click `START_WINDOWS.bat`

**Mac / Linux:**
```bash
chmod +x START_MAC_LINUX.sh && ./START_MAC_LINUX.sh
```

**Manual:**
```bash
pip install flask flask-cors
python api/index.py
```
Then open: **http://127.0.0.1:5000**

---

## Deploy to Vercel (Step by Step)

### Step 1 -- Push to GitHub

```bash
# In the project folder (where vercel.json is):
git init
git add .
git commit -m "Initial commit - InnaIT IAM Audit Platform"

# Create repo on github.com (can be PRIVATE), then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2 -- Connect to Vercel

1. Go to **https://vercel.com** and sign in (use GitHub login)
2. Click **"Add New Project"**
3. Click **"Import Git Repository"**
4. Select your repo (private repos work fine -- Vercel has access)
5. Click **"Import"**

### Step 3 -- Configure Project Settings

In the Vercel import screen:
- **Framework Preset**: select **"Other"**
- **Root Directory**: leave as `.` (default)
- **Build Command**: leave **empty**
- **Output Directory**: leave **empty**
- **Install Command**: leave **empty**

Click **"Deploy"**

### Step 4 -- Done

Vercel will give you a live URL like:
```
https://innait-iam-audit.vercel.app
```

That's it. Every time you `git push`, Vercel auto-redeploys.

---

## Project Structure (for Vercel)

```
innait-audit/
├── vercel.json             <- Tells Vercel how to route everything
├── requirements.txt        <- Python dependencies
├── .gitignore
├── README.md
├── START_WINDOWS.bat       <- Local run (Windows)
├── START_MAC_LINUX.sh      <- Local run (Mac/Linux)
└── api/
    ├── index.py            <- Flask app (Vercel entrypoint)
    ├── audit_data.py       <- All 11 modules, 100 questions
    └── frontend.html       <- React SPA served by Flask
```

---

## Modules

| Module | InnaIT Product | Priority |
|---|---|---|
| MFA & Enterprise SSO | 2FA \| eSSO | Critical |
| Windows AD Login | BioAD | Critical |
| Local Windows Login | BioWinLogin | High |
| Password Management | Password Manager | High |
| Linux Server Admin | BioNIX | Critical |
| File & Data Security | Vault | High |
| Time & Attendance | TAS | Medium |
| Event Verification | EVS | Medium |
| App Integration | InnaIT Core SDK | High |
| Hardware Security Key | InnaITKey (Precision Group) | High |
| IAM Governance | InnaIT Platform | High |

---

## Notes

- **Private repo on GitHub**: Yes, works fine with Vercel. Vercel gets OAuth access to your GitHub.
- **Sessions**: In-memory (stateless per Vercel invocation). For persistent sessions, swap for a database.
- **Custom domain**: In Vercel dashboard -> Project Settings -> Domains -> Add your domain.
