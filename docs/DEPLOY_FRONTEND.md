# Deploying Frontend Online

This guide covers multiple approaches to make your frontend accessible online, from quickest (tunneling) to production-ready deployments.

## Quick Overview

| Method | Time to Deploy | Cost | Best For |
|--------|----------------|------|----------|
| **Cloudflare Tunnel** | 5 min | Free | Development, demos, sharing with team |
| **ngrok** | 2 min | Free tier | Quick testing, webhooks |
| **Vercel** | 10 min | Free tier | React/Next.js production apps |
| **Netlify** | 10 min | Free tier | Static sites, React apps |
| **Railway** | 15 min | Free tier | Full-stack apps (backend + frontend) |
| **VPS (DigitalOcean/Linode)** | 30+ min | $5-10/mo | Full control, production |

---

## Option 1: Cloudflare Tunnel (Recommended for Development)

**Best for**: Quickly sharing your local development server online with HTTPS

### Setup (One-time)

```bash
# 1. Install cloudflared
# On Ubuntu/Debian:
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# On macOS:
brew install cloudflare/cloudflare/cloudflared

# 2. Authenticate (opens browser)
cloudflared tunnel login
```

### For React Frontend (port 5173)

```bash
# Terminal 1: Start backend
uv run python src/api_server.py

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Create tunnel
cloudflared tunnel --url http://localhost:5173
```

You'll get a public URL like: `https://random-words.trycloudflare.com`

### For Gradio (port 7860)

```bash
# Terminal 1: Start Gradio
uv run python src/gradio_app.py

# Terminal 2: Create tunnel
cloudflared tunnel --url http://localhost:7860
```

### For Next.js Chatbot (port 3000)

```bash
# Terminal 1: Start chatbot
cd chatbot
pnpm dev

# Terminal 2: Create tunnel
cloudflared tunnel --url http://localhost:3000
```

### Important: Expose Backend Too

Your frontend needs to connect to the backend. You have two options:

**Option A: Tunnel both frontend and backend separately**
```bash
# Terminal 1: Backend
uv run python src/api_server.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Backend tunnel
cloudflared tunnel --url http://localhost:8000
# Note the URL (e.g., https://backend-xyz.trycloudflare.com)

# Terminal 4: Frontend tunnel
cloudflared tunnel --url http://localhost:5173
# Note the URL (e.g., https://frontend-abc.trycloudflare.com)

# Terminal 5: Update frontend API URL
# Edit frontend/src/services/api.js to use backend tunnel URL
```

**Option B: Use Gradio (simpler - single service)**
```bash
# Just run Gradio and tunnel it (backend included)
uv run python src/gradio_app.py
cloudflared tunnel --url http://localhost:7860
```

---

## Option 2: ngrok (Alternative Tunneling)

**Best for**: Quick sharing, webhook testing

### Setup

```bash
# 1. Install ngrok
# Download from https://ngrok.com/download
# Or on Ubuntu:
snap install ngrok

# 2. Sign up at https://ngrok.com and get auth token
ngrok authtoken YOUR_AUTH_TOKEN
```

### Usage

```bash
# Tunnel frontend
ngrok http 5173

# Tunnel backend (in separate terminal)
ngrok http 8000

# Tunnel Gradio
ngrok http 7860
```

You'll get URLs like: `https://abc123.ngrok-free.app`

---

## Option 3: Vercel (Best for React/Next.js Production)

**Best for**: Production deployment of React frontend or Next.js chatbot

### Deploy React Frontend

```bash
cd frontend

# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? eof-mcp-frontend
# - Directory? ./
# - Override settings? No
```

### Deploy Next.js Chatbot

```bash
cd chatbot

# 1. Deploy
vercel

# Vercel auto-detects Next.js and configures everything
```

### Configure Environment Variables

After deployment, add environment variables in Vercel dashboard:

1. Go to your project on [vercel.com](https://vercel.com)
2. Settings → Environment Variables
3. Add:
   - `VITE_API_URL=https://your-backend-url.com` (for React)
   - `ANTHROPIC_API_KEY=your-key` (for Next.js)
   - Any other `.env` variables

### Update Frontend API URL

**For React frontend**, edit [frontend/.env.production](frontend/.env.production):
```bash
VITE_API_URL=https://your-backend-url.com
```

**For Next.js**, add to [chatbot/.env](chatbot/.env):
```bash
ANTHROPIC_API_KEY=sk-ant-...
# Other env vars from .env.example
```

---

## Option 4: Netlify (Alternative to Vercel)

**Best for**: Static sites, React apps

### Deploy React Frontend

```bash
cd frontend

# 1. Build production version
npm run build

# 2. Install Netlify CLI
npm i -g netlify-cli

# 3. Deploy
netlify deploy --prod

# Follow prompts:
# - Create new site? Yes
# - Publish directory? dist
```

### Configure Environment Variables

Add in Netlify dashboard:
- Site settings → Environment variables
- Add `VITE_API_URL=https://your-backend-url.com`

### Rebuild

```bash
# After env var changes:
npm run build
netlify deploy --prod
```

---

## Option 5: Railway (Full-Stack Deployment)

**Best for**: Deploying both backend AND frontend together

### Deploy Backend (FastAPI)

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub repo
4. Add environment variables:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ACCESS_KEY_ID=your-s3-key
   SECRET_ACCESS_KEY=your-s3-secret
   ```
5. Set start command:
   ```bash
   uv run python src/api_server.py
   ```
6. Railway will give you a URL like: `https://your-app.railway.app`

### Deploy Frontend

1. In same project, click "New Service"
2. Choose "Empty Service"
3. Connect same repo
4. Set:
   - Root directory: `frontend`
   - Build command: `npm install && npm run build`
   - Start command: `npm run preview` (or use nginx for production)
5. Add environment variable:
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   ```

---

## Option 6: VPS (DigitalOcean, Linode, AWS)

**Best for**: Full control, production deployments

### Setup on Ubuntu Server

```bash
# 1. SSH into your VPS
ssh root@your-server-ip

# 2. Install dependencies
apt update
apt install -y python3-pip nodejs npm nginx certbot python3-certbot-nginx

# 3. Clone your repo
git clone https://github.com/yourusername/eof-mcp.git
cd eof-mcp

# 4. Install Python dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
uv sync

# 5. Setup environment variables
cp .env.example .env
nano .env  # Add your API keys

# 6. Build frontend
cd frontend
npm install
npm run build

# 7. Setup nginx
sudo nano /etc/nginx/sites-available/eof-mcp
```

**Nginx config** (`/etc/nginx/sites-available/eof-mcp`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /root/eof-mcp/frontend/dist;
        try_files $uri /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# 8. Enable site
sudo ln -s /etc/nginx/sites-available/eof-mcp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 9. Setup SSL with Let's Encrypt
sudo certbot --nginx -d your-domain.com

# 10. Setup systemd service for backend
sudo nano /etc/systemd/system/eof-mcp-api.service
```

**Systemd service** (`/etc/systemd/system/eof-mcp-api.service`):
```ini
[Unit]
Description=EOF MCP API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/eof-mcp
Environment="PATH=/root/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/root/.cargo/bin/uv run python src/api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 11. Start service
sudo systemctl daemon-reload
sudo systemctl enable eof-mcp-api
sudo systemctl start eof-mcp-api

# 12. Check status
sudo systemctl status eof-mcp-api
```

Now your app is live at `https://your-domain.com`!

---

## Choosing the Right Approach

### For Quick Demos/Testing
→ **Cloudflare Tunnel** or **ngrok**
- Pros: Instant, free, HTTPS included
- Cons: URL changes on restart, not for production

### For Production React Frontend
→ **Vercel** or **Netlify**
- Pros: Free tier, auto-deploys on git push, CDN, HTTPS
- Cons: Need separate backend hosting

### For Production Full-Stack
→ **Railway** or **VPS**
- Pros: Backend + frontend together, full control
- Cons: Costs money, more setup

### For Next.js Chatbot
→ **Vercel** (made by same team)
- Pros: Perfect Next.js integration, edge functions, database support
- Cons: Need to configure database separately

---

## Security Considerations

### 1. CORS Configuration
Update [src/config.yaml](../src/config.yaml):
```yaml
api:
  cors_origins:
    - "https://your-frontend-domain.com"
    - "http://localhost:5173"  # Keep for local dev
```

### 2. Environment Variables
**Never commit** `.env` to git. Always use:
- Vercel/Netlify: Dashboard environment variables
- Railway: Project settings → Variables
- VPS: `.env` file with proper permissions (`chmod 600 .env`)

### 3. Rate Limiting
For production, add rate limiting to FastAPI:

```bash
cd /home/ubuntu/project/eof-mcp
uv add slowapi
```

Then edit [src/api_server.py](../src/api_server.py):
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/chat/send")
@limiter.limit("10/minute")  # 10 requests per minute
async def send_message(request: Request, ...):
    # ... existing code
```

### 4. API Key Protection
Use environment variables for all sensitive keys:
```bash
# In .env (never commit!)
ANTHROPIC_API_KEY=sk-ant-...
ACCESS_KEY_ID=...
SECRET_ACCESS_KEY=...
```

---

## Monitoring & Logs

### Check Backend Logs (VPS)
```bash
sudo journalctl -u eof-mcp-api -f
```

### Check Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Vercel/Railway Logs
Available in their dashboards with real-time streaming.

---

## Cost Comparison

| Service | Free Tier | Paid Plans |
|---------|-----------|------------|
| **Cloudflare Tunnel** | Unlimited | Free forever |
| **ngrok** | 1 tunnel, random URLs | $8/mo (custom domains) |
| **Vercel** | 100GB bandwidth/mo | $20/mo (Pro) |
| **Netlify** | 100GB bandwidth/mo | $19/mo (Pro) |
| **Railway** | $5 free credit/mo | $5-20/mo typical |
| **DigitalOcean** | None | $6/mo (1GB RAM) |

---

## Troubleshooting

### Frontend can't connect to backend
1. Check CORS settings in [src/config.yaml](../src/config.yaml)
2. Verify `VITE_API_URL` environment variable
3. Check browser console for CORS errors
4. Ensure backend is accessible (test with curl)

### Tunnel disconnects
- Cloudflare tunnels close when terminal closes
- Use `screen` or `tmux` to keep processes alive:
  ```bash
  screen -S tunnel
  cloudflared tunnel --url http://localhost:5173
  # Press Ctrl+A, then D to detach
  # Reconnect with: screen -r tunnel
  ```

### SSL certificate errors
```bash
# Renew Let's Encrypt certificate
sudo certbot renew
```

### Backend not starting
```bash
# Check logs
sudo journalctl -u eof-mcp-api -n 50

# Test manually
cd /home/ubuntu/project/eof-mcp
uv run python src/api_server.py
```

---

## Next Steps

1. **Choose your deployment method** based on the comparison above
2. **Set up environment variables** securely
3. **Update CORS settings** to allow your frontend domain
4. **Test thoroughly** before sharing publicly
5. **Monitor logs** for errors and performance issues

For more help, see:
- [docs/API_USAGE.md](API_USAGE.md) - API documentation
- [docs/QUICK_START.md](QUICK_START.md) - Development setup
- [docs/CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) - Configuration options
