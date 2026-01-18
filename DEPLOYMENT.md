# 🚀 Deployment Guide

## Quick Deploy to Railway (Recommended - Easiest)

Railway offers the simplest deployment with automatic HTTPS and custom domains.

### Step 1: Prepare Your Code

1. Make sure all files are in the `oman-address-api` folder
2. You should have:
   - `main.py`
   - `requirements.txt`
   - `README.md`

### Step 2: Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository (or create new one)
6. Railway will automatically:
   - Detect Python
   - Install requirements
   - Start the app

### Step 3: Configure

1. Add environment variables (if needed):
   - Go to your project → Variables
   - Add any secrets (none needed for MVP)

2. Get your URL:
   - Railway provides: `https://your-app.up.railway.app`
   - Or add custom domain in Settings

### Step 4: Test

```bash
curl https://your-app.up.railway.app/stats
```

**Cost:** Free tier available, then $5/month for hobby projects

---

## Alternative: Deploy to Render

### Step 1: Create account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### Step 2: New Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repo
3. Configure:
   - **Name:** oman-address-api
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3: Deploy

Render will build and deploy automatically.

**Cost:** Free tier available (sleeps after inactivity), then $7/month

---

## Alternative: DigitalOcean App Platform

### Step 1: Create Droplet

1. Go to [digitalocean.com](https://digitalocean.com)
2. Create new App
3. Connect GitHub

### Step 2: Configure

1. Select your repo
2. Choose Python
3. Use default build settings

**Cost:** $5/month minimum

---

## Local Development

### Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

### Access

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin

---

## Production Considerations

### 1. Database

**Current:** SQLite (file-based)
**For production:** Migrate to PostgreSQL

Railway/Render both offer managed PostgreSQL:
```bash
# In Railway, add PostgreSQL plugin
# Get connection string from dashboard
```

Update code to use environment variable:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///oman_addresses.db")
```

### 2. Security

**Add these for production:**

```python
# In main.py, add:
import os

# Only allow specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "*").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (install slowapi)
from slowapi import Limiter
limiter = Limiter(key_func=lambda: "global")
```

### 3. Monitoring

**Add logging:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use in endpoints
logger.info(f"Address registered: {address_code}")
```

**Use external monitoring:**
- Railway: Built-in metrics
- Render: Built-in logs
- Or: [Sentry](https://sentry.io) for error tracking

### 4. Backups

**For SQLite:**
```bash
# Daily backup script
#!/bin/bash
cp oman_addresses.db backups/backup_$(date +%Y%m%d).db
```

**For PostgreSQL:**
Managed services handle backups automatically.

### 5. Custom Domain

**In Railway:**
1. Go to Settings → Domains
2. Add your domain (omanaddress.com)
3. Update DNS records as shown

**SSL:** Automatic with Railway/Render

---

## Environment Variables

Create `.env` file for local development:

```bash
# .env
DATABASE_URL=sqlite:///oman_addresses.db
ALLOWED_ORIGINS=https://omanaddress.com,https://www.omanaddress.com
```

For production, set these in Railway/Render dashboard.

---

## Testing Deployment

Once deployed, test all endpoints:

```bash
# Set your production URL
URL="https://your-app.up.railway.app"

# Test stats
curl $URL/stats

# Test registration
curl -X POST $URL/api/register-address \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "96891234567",
    "latitude": 23.5880,
    "longitude": 58.3829,
    "city": "Muscat",
    "area": "Al Khuwair"
  }'

# Get API key
curl -X POST $URL/api/request-key \
  -H "Content-Type: application/json" \
  -d '{"partner_name": "Test Restaurant"}'

# Test lookup (use your API key)
curl "$URL/api/lookup?phone=96891234567&X-API-Key=YOUR_KEY_HERE"
```

---

## Scaling Considerations

**Current capacity:** 100-1000 requests/day easy

**When you hit limits:**

1. **Database:** Migrate to PostgreSQL with connection pooling
2. **Caching:** Add Redis for frequent lookups
3. **Multiple instances:** Railway/Render auto-scale
4. **CDN:** Use Cloudflare for static assets

**Expected cost at scale:**
- 10k addresses, 1k lookups/day: $20-40/month
- 100k addresses, 10k lookups/day: $100-200/month

---

## Maintenance

### Weekly:
- Check error logs
- Review failed deliveries
- Backup database

### Monthly:
- Review usage stats
- Check for suspicious API keys
- Update dependencies

### Quarterly:
- Review pricing
- Analyze growth metrics
- Plan new features

---

## Next Steps After Deployment

1. ✅ Deploy to Railway/Render
2. ✅ Get custom domain
3. ✅ Create simple landing page
4. ✅ Test all endpoints
5. ✅ Share URL with first test users

---

## Troubleshooting

**Port issues:**
```python
# Make sure using PORT from environment
port = int(os.getenv("PORT", 8000))
uvicorn.run(app, host="0.0.0.0", port=port)
```

**Database locked:**
- SQLite doesn't handle concurrent writes well
- Migrate to PostgreSQL for production

**CORS errors:**
- Check allowed_origins in CORS middleware
- Make sure frontend URL is whitelisted

---

## Support

If you hit issues:
1. Check Railway/Render logs
2. Review error messages in `/docs` endpoint
3. Test locally first
4. Verify environment variables

Good luck! 🚀
