# Deployment Guide

This project is ready to deploy with:

- Backend on Railway
- Frontend on Vercel
- Database and image storage on Supabase

## 1. Rotate exposed secrets

If you pasted your Telegram bot token or Gemini API key into chat, rotate them before deployment.

## 2. Fill the empty environment variables

### Backend local `.env`

Use these values while developing locally:

```env
APP_ENV=development
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
SUPABASE_PRODUCTS_TABLE=products
SUPABASE_SALES_TABLE=sales
SUPABASE_STORAGE_BUCKET=product-images
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
BACKEND_PUBLIC_URL=http://localhost:8000
FRONTEND_APP_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
TELEGRAM_BOT_TOKEN=optional
```

### Frontend local `.env`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username
```

### Where to find the empty Supabase values

- `SUPABASE_URL`: Supabase dashboard -> Project Settings -> API -> Project URL
- `SUPABASE_KEY`: Supabase dashboard -> Project Settings -> API -> `service_role` secret key

Use the `service_role` key on the backend only. Do not put it in Vercel frontend variables.

## 3. Local production-like verification

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Check:

- `GET http://localhost:8000/health`
- `POST /api/v1/products/onboard`
- `POST /api/v1/products/match`
- `POST /api/v1/sales`
- `GET /api/v1/dashboard/summary`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## 4. Railway backend deployment

Create a Railway service from this repo and set the service root to `backend/`.

Railway will use the Dockerfile at `backend/Dockerfile`.

Set these Railway variables:

```env
APP_ENV=production
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
SUPABASE_PRODUCTS_TABLE=products
SUPABASE_SALES_TABLE=sales
SUPABASE_STORAGE_BUCKET=product-images
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
BACKEND_PUBLIC_URL=https://your-railway-backend.up.railway.app
FRONTEND_APP_URL=https://your-vercel-frontend.vercel.app
CORS_ORIGINS=https://your-vercel-frontend.vercel.app
```

Optional:

- `TELEGRAM_BOT_TOKEN` only if you also want the legacy bot process

After deploy, open:

- `https://your-railway-backend.up.railway.app/health`

Expected:

- `status: ok`
- `supabase_configured: true`
- `supabase_ready: true`
- `gemini_configured: true`

## 5. Vercel frontend deployment

Create a Vercel project with the root directory set to `frontend/`.

Set these Vercel environment variables:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-railway-backend.up.railway.app
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username
```

Deploy and confirm the frontend can:

- load dashboard summary
- add a product
- scan a product
- show top matches with images

## 6. Telegram Mini App setup

In BotFather:

1. Open your bot settings
2. Configure the Mini App / Web App URL
3. Point it to your Vercel production URL
4. Test from Telegram mobile

## 7. Final acceptance checklist

- Add a product from the Mini App
- Confirm the image appears from Supabase Storage
- Confirm Gemini names the product specifically
- Scan the same item again
- Confirm the correct item is in the top 3
- Confirm the image thumbnails are shown in match cards
- Confirm sale logging reduces stock
- Confirm dashboard daily profit updates
- Confirm stock turns yellow under 3 and red at 0
