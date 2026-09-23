# Render.com Deployment Guide: PreciousEdu AI Chatbot Backend

This guide explains step-by-step how to deploy your FastAPI backend to **[Render.com](https://render.com/)** and connect it to your `index.php` frontend.

---

## 1. Project Files Configured for Render

The following files are already prepared and pre-configured for Render:
- `render.yaml`: Render Blueprint configuration (auto-detects Python, build commands, and start commands).
- `backend/Procfile`: Universal process file (`web: uvicorn main:app --host 0.0.0.0 --port $PORT`).
- `backend/.env.example`: Reference for all environment variables.
- `backend/config.py`: Dynamically binds to Render's `$PORT` (typically `10000`) and supports dynamic CORS.
- `.gitignore`: Prevents sensitive files (`.env`, `site_cache.json`, `__pycache__`) from being committed to GitHub.

---

## 2. Deploying on Render (Step-by-Step)

### Option A: Using Render Blueprint (Recommended - 1 Click)

1. Push your project to GitHub.
2. Log in to [dashboard.render.com](https://dashboard.render.com/).
3. Click **New +** &rarr; **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically read `render.yaml` and configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Under **Environment Variables**, fill in your `GEMINI_API_KEYS`.
7. Click **Apply**.

---

### Option B: Manual Web Service Setup

1. Push your repository to GitHub.
2. In the Render Dashboard, click **New +** &rarr; **Web Service**.
3. Select your repository and configure:
   - **Name**: `precious-edu-chatbot-api` (or any name you prefer)
   - **Region**: Choose closest to your audience (e.g., Singapore / Frankfurt)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: `Free`

4. Scroll down to **Environment Variables** and add the following keys:

| Key | Value | Note |
|---|---|---|
| `GEMINI_API_KEYS` | `key1,key2,key3,key4` | Comma-separated list of your Gemini API keys |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Model identifier |
| `TARGET_SITE` | `https://www.preciousedu.in/` | Website to scrape for knowledge context |
| `CACHE_TTL_SECONDS` | `21600` | 6 hours cache TTL |
| `ALLOWED_ORIGINS` | `*` | Or specify your frontend domain (e.g., `https://yourdomain.com`) |

5. Click **Create Web Service**.
6. Wait 2-3 minutes for the build and deployment to complete. Render will generate your live public URL, for example:
   ```
   https://precious-edu-chatbot-api.onrender.com
   ```

---

## 3. Verify Your Live Backend

Open your browser and visit:
```
https://precious-edu-chatbot-api.onrender.com/api/health
```
You should see:
```json
{
  "status": "healthy",
  "service": "PreciousEdu Chatbot API",
  "model": "gemini-3.5-flash-lite",
  "api_keys_configured": 4,
  "target_site": "https://www.preciousedu.in/"
}
```

---

## 4. Connect Frontend (`index.php`)

Once you have your Render URL (e.g. `https://precious-edu-chatbot-api.onrender.com`), open `index.php` and set it at the top (line 10):

```php
$RENDER_BACKEND_URL = 'https://precious-edu-chatbot-api.onrender.com';
```

Now, when users visit your website, `index.php` will automatically communicate with your live Render backend!

> [!TIP]
> **Render Free Tier Spin-Down**:
> On Render's Free tier, services go to sleep after 15 minutes of inactivity. The first message after a period of sleep might take 30-45 seconds while Render spins up the container.
> The frontend UI in `index.php` is already configured with an extended 75-second timeout and shows an informative indicator (`"Connecting to server (waking up if sleeping)..."`) so your users have a smooth experience.
