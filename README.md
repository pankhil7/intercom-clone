# Intercom Clone — Full-Stack Customer Support Platform

A production-ready Intercom clone built with Python/FastAPI (backend) and React/TypeScript (frontend), featuring live chat, email support, AI summarization, knowledge base, webhooks, SLA tracking, and more.

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────┐
│  React Dashboard│────▶│  FastAPI + Socket.io  │────▶│  PostgreSQL  │
│  (Vercel)       │◀────│  (Railway)            │◀────│              │
└─────────────────┘     └──────────────────────┘     └──────────────┘
         ▲                        ▲
         │                        │ Webhooks / Email
┌─────────────────┐     ┌──────────────────────┐
│  Vanilla JS     │     │  Mailgun / Cloudmailin│
│  Widget (CDN)   │     │  Groq AI (Llama 3)   │
└─────────────────┘     └──────────────────────┘
```

### Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, python-socketio, SQLAlchemy, Alembic |
| Database | PostgreSQL (JSONB, ARRAY, TSVECTOR for FTS) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query |
| Real-time | Socket.io (`/agent` + `/widget` namespaces) |
| Email | Cloudmailin (inbound) + Mailgun (outbound) |
| AI | Groq API (Llama 3, free tier) with RAG over KB articles |
| Widget | Vanilla TypeScript, compiled to IIFE bundle via Vite |
| Deployment | Railway (backend) + Vercel (frontend) |

## Features

### Core
- **Auth & Team Management** — JWT + refresh tokens, invite-based signup, role-based access (admin/agent)
- **Live Chat Widget** — Embeddable JS snippet, real-time via Socket.io, session persistence
- **Email Channel** — Inbound via Cloudmailin webhook, outbound via Mailgun, full thread linking
- **Unified Inbox** — Filter by status/channel/assignee, SLA breach indicators, real-time updates
- **Knowledge Base** — Category + article CRUD, TipTap rich editor, PostgreSQL full-text search
- **AI Summarization** — Groq/Llama 3 conversation summaries with sentiment analysis
- **Custom Domains** — TXT record verification for KB hosting on your domain

### Stretch
- **AI Auto-Reply Drafts** — RAG-backed draft suggestions (human-reviews before sending)
- **Canned Responses** — Shortcut-triggered templates, "/" picker in reply box
- **Contact Timeline** — Full activity log: messages, page views, conversation events
- **SLA Tracking** — Configurable first-response + resolution windows, breach alerts
- **Webhooks & API** — HMAC-SHA256 signed webhooks, REST API keys, 5-attempt retry queue
- **Analytics Dashboard** — Resolution rate chart, heatmap, agent performance table

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Copy and fill environment variables
cp .env.example .env.local

# Start dev server
npm run dev
```

### Widget

```bash
cd widget
npm install
npm run build    # outputs dist/widget.iife.js
```

Open `widget/demo.html` (after building) to test locally.

## Environment Variables

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/intercom_clone
SECRET_KEY=your-secret-key-min-32-chars
WIDGET_SECRET_KEY=your-widget-secret-key
GROQ_API_KEY=gsk_...
MAILGUN_API_KEY=key-...
MAILGUN_DOMAIN=mg.yourcompany.com
MAILGUN_FROM_EMAIL=support@yourcompany.com
CLOUDMAILIN_SECRET=your-cloudmailin-secret
CLOUDMAILIN_ADDRESS=your-address@cloudmailin.net
FRONTEND_URL=https://yourapp.vercel.app
WIDGET_CDN_URL=https://widget.yourapp.com
```

### Frontend (`frontend/.env.local`)

```env
VITE_API_BASE_URL=https://your-api.railway.app/api/v1
VITE_SOCKET_URL=https://your-api.railway.app
VITE_WIDGET_URL=https://widget.yourapp.com
```

## Deployment

### Backend → Railway

1. Create a Railway project, add PostgreSQL plugin
2. Set all env vars from `backend/.env.example`
3. Connect your GitHub repo — Railway auto-deploys on push
4. The `railway.toml` configures the Dockerfile build

### Frontend → Vercel

1. Import repo in Vercel, set root directory to `frontend`
2. Set `VITE_API_BASE_URL` and `VITE_SOCKET_URL` env vars
3. `vercel.json` handles SPA routing rewrites

### Widget → CDN

Build the widget (`npm run build` in `widget/`) and upload `dist/widget.iife.js` to any CDN (Cloudflare R2, S3, etc.).

## Widget Integration

```html
<script>
  window.InboxWidget = {
    widgetKey: 'YOUR_WIDGET_KEY',      // from Settings → Inboxes
    primaryColor: '#4f46e5',           // optional, defaults to indigo
    greeting: 'Hi! How can we help?', // optional
  };
</script>
<script src="https://your-cdn.com/widget.iife.js" async></script>
```

## API Authentication

All dashboard API calls use `Authorization: Bearer <jwt>`.

For programmatic access, create an API key in Settings → API Keys:
```
Authorization: Bearer sk_live_...
```

## Known Limitations

1. **Socket.io + Railway**: Railway doesn't support sticky sessions by default — if you scale to multiple instances, add Redis adapter for socket.io (`socket.io-adapter-redis`). The code uses `redis_url` from config for this.
2. **Email deliverability**: Mailgun sandbox mode limits recipients. Add a verified domain in Mailgun for production.
3. **Groq rate limits**: Free tier is 30 RPM / 6,000 RPD. The AI service has a 10-minute response cache to reduce calls.
4. **Widget CORS**: Set `FRONTEND_URL` and ensure your widget CDN domain is in the CORS allowed origins in `app/main.py`.
5. **Custom domains**: TXT verification is implemented; CNAME routing requires a reverse proxy (nginx/Caddy) config not included here.
