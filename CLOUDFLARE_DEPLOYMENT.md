# Cloudflare Pages Deployment Guide — DecodeX DLD-SOC

*A proprietary work product of **DecodeX Security Technologies Private Limited**.*  
*Copyright (c) 2026 DecodeX Security Technologies Private Limited. All rights reserved.*

---

## 🌐 Overview

The **DecodeX Data Leakage Detection & Cyber Attribution Platform (DLD-SOC)** frontend is built with React 19 and Vite. It is optimized for high-performance deployment on **Cloudflare Pages** with:
- Zero-configuration Single Page Application (SPA) routing via `_redirects`
- Production HTTP security headers via `_headers`
- Dual-mode operation: **Live API Mode** when connected to a deployed backend, and **Interactive Standby Demo Mode** when running standalone or in preview.

---

## 🚀 Deployment Method 1: Cloudflare Pages Dashboard (Git Integration — Recommended)

This is the recommended continuous deployment method. Any push to your Git repository automatically triggers a build and deploy.

### Step 1: Connect Repository
1. Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. In the left navigation, select **Compute (Workers & Pages)** > **Pages**.
3. Click **Create a project** > **Connect to Git**.
4. Select your GitHub repository: `Decoder420/data-leakage-detection`.

### Step 2: Configure Build Settings
Fill in the build configuration:

| Setting | Value | Notes |
|---|---|---|
| **Project name** | `decodex-dld-soc` | (or your preferred name) |
| **Production branch** | `main` | |
| **Framework preset** | `Vite` | |
| **Root directory** | `frontend` | ⚠️ **Crucial**: Must point to `frontend` |
| **Build command** | `npm run build` | |
| **Build output directory** | `dist` | |

### Step 3: Configure Environment Variables (Optional)
Under **Environment variables (advanced)**, add:

| Variable | Value | Description |
|---|---|---|
| `VITE_API_URL` | `https://api.yourdomain.com` | URL of your deployed FastAPI backend |
| `NODE_VERSION` | `20` | Recommended Node.js runtime |

> [!NOTE]
> If you do not have a live backend deployed yet, you can leave `VITE_API_URL` blank. The frontend will run in **Interactive Standby Demo Mode**, allowing full exploration of the Guilt Gauge, Breach Simulator, and Smart Allocation matrix. You can also configure the backend URL live anytime via the in-app **Live API Status** button in the header.

### Step 4: Deploy
Click **Save and Deploy**. Cloudflare will build the site in ~30 seconds and provide a live URL (e.g. `https://decodex-dld-soc.pages.dev`).

---

## ⚡ Deployment Method 2: Direct CLI Deployment via Wrangler

If you prefer to deploy pre-built assets directly from your terminal:

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Build the production bundle
npm run build

# 3. Deploy directly to Cloudflare Pages
npx wrangler pages deploy dist --project-name=decodex-dld-soc
```

Follow the terminal prompts to authenticate with Cloudflare on first run.

---

## 🔒 Backend Deployment & Connecting to Cloudflare

The FastAPI Attribution Engine (`backend/`) can be hosted on any cloud container host:

### Option A: Render (Free/Starter Web Service)
1. Create a **New Web Service** from `Decoder420/data-leakage-detection`.
2. Set **Build Command**: `pip install -r backend/requirements.txt`
3. Set **Start Command**: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Copy the service URL (e.g., `https://decodex-dld-api.onrender.com`) and set it as `VITE_API_URL` in Cloudflare Pages.

### Option B: Railway / Fly.io / Docker
Deploy using the included root `Dockerfile.backend`:
```bash
docker build -f Dockerfile.backend -t decodex-dld-api .
docker run -p 8000:8000 decodex-dld-api
```

### Option C: In-App Live API Reconnection
Once your Cloudflare Pages site is live, open the application in your browser:
1. Look at the top right header next to the Dataset Selector.
2. Click the **Standby Demo / Live API** pill button.
3. Enter your backend API Base URL (e.g. `https://api.yourdomain.com`).
4. Click **Test Connection** to verify health.
5. Click **Save & Apply** — the URL is stored in your browser's `localStorage` and automatically connects to the live backend without needing a redeploy!

---

## ✅ Pre-Deployment Verification Checklist

- [x] **React 19 Hook Order**: All modal components adhere to React Rules of Hooks (0 lint errors).
- [x] **Frontend Production Build**: `npm run build` compiles cleanly into `dist/`.
- [x] **SPA Routing**: `_redirects` file exists in `dist/_redirects` to route all paths to `/index.html 200`.
- [x] **Security Headers**: `_headers` configured with `X-Frame-Options`, `X-Content-Type-Options`, and cache policy.
- [x] **Branding & Assets**: Official DecodeX logos, wordmarks, icons, and copyright notices embedded.
- [x] **Simulation & Allocation Routes**: Full compatibility with both `/api/v1` and legacy frontend paths.
- [x] **Backend Unit Tests**: 17/17 tests passing via `pytest`.

---

*DecodeX Security Technologies Private Limited — Confidential & Proprietary.*
