# Zembil Vision

Sticker-less, visual-first inventory for Telegram-first commerce.

This repository now includes a deployable MVP:

- `backend/`: FastAPI service for onboarding products, visual similarity search, and sales logging
- `frontend/`: Next.js Telegram Mini App for adding products, scanning sold items, and viewing the lazy accountant dashboard
- `backend/app/bot.py`: optional legacy bot flow kept as a fallback
- `supabase/schema.sql`: schema with `pgvector`
- `DEPLOYMENT.md`: production setup for Railway, Vercel, and Supabase

## MVP scope

The current MVP focuses on:

1. Seller sends a product photo
2. AI suggests a title and category
3. Seller confirms purchase price, sale price, and quantity
4. Product image is stored in Supabase Storage
5. Product is stored with an embedding-ready visual fingerprint for future checkout matching
5. Seller scans sold items in the Mini App and confirms one of the top 3 visual matches
6. Dashboard shows daily profit and stock alerts in the same Mini App

## Local setup

### 1. Environment

Copy:

- [backend/.env.example](/C:/Users/Admin/Desktop/Teleshop/backend/.env.example) -> `backend/.env`
- [frontend/.env.example](/C:/Users/Admin/Desktop/Teleshop/frontend/.env.example) -> `frontend/.env`

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Telegram Mini App

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` locally or load the deployed URL inside Telegram as a Mini App.

### 4. Optional Telegram bot

- `/start` shows the available flows
- `/add` starts product onboarding
- `/scan` identifies an item from a photo and logs a sale
- `/cancel` exits the current conversation

```bash
cd backend
.venv\Scripts\activate
python -m app.bot
```

### 5. Frontend

## Core flows

### Product onboarding

- `POST /api/v1/products/onboard`
- Accepts an uploaded image plus `cost_price`, `sale_price`, and `stock_qty`
- Calls Gemini to describe the image
- Uploads the image to Supabase Storage
- Generates an embedding
- Persists the product record in Supabase

### Checkout recognition

- `POST /api/v1/products/match`
- Accepts a checkout photo
- Embeds the image
- Returns the top 3 visually similar items

### Sale confirmation

- `POST /api/v1/sales`
- Confirms the chosen item
- Decrements stock
- Logs profit

### Dashboard summary

- `GET /api/v1/dashboard/summary`
- Returns total daily profit, sales count, total products, and red/yellow stock alerts

## Notes

- Development mode still includes local fallbacks, but production mode requires Supabase, Gemini, and explicit CORS configuration.
- Supabase RPC names in the code expect the SQL in `supabase/schema.sql`.
- Full deployment steps live in [DEPLOYMENT.md](/C:/Users/Admin/Desktop/Teleshop/DEPLOYMENT.md:1).
