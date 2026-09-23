# PreciousEdu AI Chatbot — Decoupled Full-Stack Architecture

An enterprise-ready, decoupled AI Chatbot solution for **[Precious Education](https://www.preciousedu.in/)**. Built with a high-performance **Python FastAPI** backend communicating with **Google Gemini (`gemini-3.5-flash-lite`)** and a responsive, lightweight **PHP** frontend.

---

## 🌟 Key Features

- **Dynamic Gemini API Key Rotation (`GEMINI_API_1`, `GEMINI_API_2`, ...)**:
  - Dynamically fetches keys from `.env` or Render environment variables in sequential order (`GEMINI_API_1`, `GEMINI_API_2`, `GEMINI_API_3`, `GEMINI_API_4`, ...).
  - Automatically fails over to the next key if quota (HTTP 429), rate-limits, or authentication issues occur.
- **Asynchronous Web Scraping & Intelligent Caching**:
  - Concurrently fetches target pages from `https://www.preciousedu.in/` using `httpx` and `BeautifulSoup4`.
  - Caches scraped content to disk for 6 hours (configurable) to ensure lightning-fast responses.
- **WhatsApp Lead Collection Fast-Path**:
  - Automatically identifies lead queries (e.g., *"Can I share my details here?"*) and responds instantly with positive confirmation.
- **Enterprise-Grade Security**:
  - **Zero Key Leakage**: API keys are completely masked in console/system logs (e.g., `AQ.A...FTsQ`).
  - **Error Sanitizer**: All error messages and stack traces are scrubbed of API key strings before returning to clients.
  - **Input Sanitization & Length Limits**: Enforces a 2,000-character ceiling and a 20-turn conversation history cap to guard against token budget exploits and buffer overflow abuse.
  - **Security Headers**: Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `Referrer-Policy` headers.
  - **Strict `.gitignore`**: Protects `.env`, credentials, logs, and temporary caches from being exposed to GitHub.
- **Production & Render.com Ready**:
  - Includes `render.yaml` (Blueprint), `backend/Procfile`, dynamic `$PORT` binding, and CORS configuration.

---

## 📁 Project Architecture

```
Using API/
├── backend/
│   ├── .env                      # Local environment secrets (ignored by git)
│   ├── .env.example              # Template for Render / production env vars
│   ├── config.py                 # Central config, dynamic key loader & masking
│   ├── gemini_service.py         # Multi-key rotation & Gemini communication
│   ├── main.py                   # FastAPI application, CORS & security middleware
│   ├── Procfile                  # Universal web dyno start command
│   ├── requirements.txt          # Python dependencies
│   ├── run_backend.bat           # Windows one-click local launcher
│   ├── scraper.py                # Async web scraper & cache manager
│   ├── test_backend.py           # Comprehensive integration & security test suite
│   └── test_rotation.py          # Key fallback rotation simulation test
├── index.php                     # Pure frontend UI (clean HTML/CSS/JavaScript)
├── .gitignore                    # Comprehensive git exclusion rules
├── render.yaml                   # Render.com Blueprint configuration
├── RENDER_DEPLOYMENT.md          # Step-by-step Render deployment guide
└── README.md                     # Project documentation
```

---

## ⚙️ Environment Configuration (`backend/.env`)

Configure individual keys in `backend/.env`. You can add as many keys as you need:

```env
# Gemini API Keys (Sequentially checked and rotated)
GEMINI_API_1=your_first_gemini_api_key_here
GEMINI_API_2=your_second_gemini_api_key_here
GEMINI_API_3=your_third_gemini_api_key_here
GEMINI_API_4=your_fourth_gemini_api_key_here

# Model Configuration
GEMINI_MODEL=gemini-3.5-flash-lite

# Website Knowledge Base Scraper
TARGET_SITE=https://www.preciousedu.in/
CACHE_TTL_SECONDS=21600

# Server Settings
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=*
```

---

## 🚀 Quick Start (Local Development)

### 1. Install Dependencies
Ensure Python 3.10+ is installed:
```powershell
cd backend
pip install -r requirements.txt
```

### 2. Start the FastAPI Backend
Double-click `backend/run_backend.bat` or run:
```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- Health Check: `http://localhost:8000/api/health`
- Interactive Swagger API Docs: `http://localhost:8000/docs`

### 3. Launch Frontend (`index.php`)
Serve `index.php` with PHP's built-in server or Apache/XAMPP:
```powershell
php -S localhost:8080
```
Open `http://localhost:8080/index.php` in your browser.

---

## 🌐 Deploying to Render.com

Full deployment instructions are available in **[RENDER_DEPLOYMENT.md](file:///c:/Users/Lenovo/Desktop/Ritesh%20Gajjar%20Work/Precious%20Edu%20LLM/Using%20API/Using%20API/RENDER_DEPLOYMENT.md)**.

### Summary:
1. Push this repository to GitHub (the included `.gitignore` guarantees that `.env` will never be pushed).
2. On [Render Dashboard](https://dashboard.render.com/), create a **New Web Service**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. In **Environment Variables**, add:
   - `GEMINI_API_1`: *(Your 1st Gemini key)*
   - `GEMINI_API_2`: *(Your 2nd Gemini key)*
   - `GEMINI_API_3`: *(Your 3rd Gemini key)*
   - `GEMINI_API_4`: *(Your 4th Gemini key)*
   - `GEMINI_MODEL`: `gemini-3.5-flash-lite`
   - `TARGET_SITE`: `https://www.preciousedu.in/`
   - `ALLOWED_ORIGINS`: `*`
4. Once deployed, copy your Render URL (e.g. `https://precious-edu-chatbot-api.onrender.com`) and paste it into line 10 of `index.php`:
   ```php
   $RENDER_BACKEND_URL = 'https://precious-edu-chatbot-api.onrender.com';
   ```

---

## 🧪 Testing & Verification

Run the automated test suites inside `backend/`:

```powershell
cd backend

# 1. Test health check, lead patterns, security length limits, and live chat
python test_backend.py

# 2. Test automatic API key fallback rotation
python test_rotation.py
```

---

## 🔒 Security Summary

| Feature | Implementation |
|---|---|
| **Secret Management** | Dynamic environment discovery (`GEMINI_API_1`..N); keys are excluded from git via `.gitignore`. |
| **Masked Logging** | Keys are masked in console output (`AQ.A...FTsQ`). |
| **Error Scrubbing** | Outgoing exceptions and error bodies are sanitized to prevent API key leakages. |
| **Anti-Abuse Controls** | Request messages capped at 2,000 characters; past context limited to 20 turns. |
| **HTTP Security** | `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`. |

---

## 📄 License
Internal project for Precious Education. All rights reserved.
