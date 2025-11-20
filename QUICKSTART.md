# Quick Start Guide

Get the scraper running in 5 minutes!

## Step 1: Install Python Dependencies (2 minutes)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

## Step 2: Setup Supabase Database (2 minutes)

1. Go to https://supabase.com and sign up (free)
2. Create a new project
3. Go to **SQL Editor** → **New Query**
4. Copy/paste content from `migrations/002_create_tiktok_table.sql`
5. Click **Run**
6. Go to **SQL Editor** again and run:
   ```sql
   ALTER TABLE public.tiktok DISABLE ROW LEVEL SECURITY;
   ```

## Step 3: Get Your Credentials (1 minute)

In Supabase dashboard:
1. Click **Project Settings** (gear icon)
2. Click **API** tab
3. Copy:
   - **URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbGci...` (long string)

## Step 4: Set Environment Variables

### Windows PowerShell:
```powershell
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_KEY="your-anon-key-here"
```

### Linux/Mac:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key-here"
```

## Step 5: Run! 🚀

```bash
python base.py
```

**Expected output:**
```
✅ Supabase client initialized successfully
✅ Scraped 93 unique hashtags
✅ Successfully uploaded 10 records total
```

## Step 6: View Your Data

Go to Supabase → **Table Editor** → **tiktok** table

You should see 10 trending hashtags!

## 🎯 That's It!

Your scraper is now running. Run `python base.py` anytime to get fresh data.

---

## ⚠️ Getting Errors?

### "Connection timed out"
**Solution:** TikTok blocked your IP. You need a proxy.

See [PROXY_SETUP.md](PROXY_SETUP.md) for:
- Free proxy lists (testing)
- Premium proxy services (production)
- Alternative solutions (VPN, mobile hotspot)

Quick fix:
```powershell
# Add proxy config
$env:PROXY_SERVER="http://proxy.example.com:8080"
$env:PROXY_USERNAME="username"
$env:PROXY_PASSWORD="password"

# Run again
python base.py
```

### "SUPABASE_URL not set"
**Solution:** Set environment variables (Step 4 above)

### "No data in Supabase"
**Solution:** Disable RLS
```sql
ALTER TABLE public.tiktok DISABLE ROW LEVEL SECURITY;
```

---

## 📚 More Information

- **Full Documentation:** [README.md](README.md)
- **Database Setup:** [SUPABASE_SETUP.md](SUPABASE_SETUP.md)
- **Proxy Configuration:** [PROXY_SETUP.md](PROXY_SETUP.md)

## 🤝 Need Help?

Check the troubleshooting sections in README.md or contact support.

Happy scraping! 🎉
