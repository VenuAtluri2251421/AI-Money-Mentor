# 🚀 Dinero: AI Money Mentor

**Dinero** is an intelligent, AI-powered personal finance platform built for the **ET AI Hackathon 2026**. It helps users take control of their finances by offering AI-driven insights, advanced financial calculators, and automated PDF portfolio extraction.

---

## ✨ Features

- **🤖 Dinero AI Advisor**: A Gemini-powered AI chatbot that understands your specific financial context, risk appetite, and goals. Ask it for personalized investment strategies or plain-English explanations of complex financial jargon.
- **📄 Smart PDF Extraction**: Upload your CAMS/KFintech mutual fund statements or Form 16s. Dinero automatically parses the documents and constructs your financial profile without manual data entry.
- **🧮 Advanced Financial Calculators**:
  - **SIP & Reverse SIP Calculators**: Plan your wealth accumulation journey.
  - **FIRE Engine**: Calculate your "Financial Independence, Retire Early" number and exactly how many years it will take to get there.
  - **Tax Comparison (Old vs New Regime)**: Quickly figure out which Income Tax regime saves you the most money.
  - **Portfolio XIRR**: Track the actual annualized returns of your investments.
- **📊 Financial Health Score**: Get an instant rating (0-100) on your financial well-being based on your savings rate, emergency fund, and debt-to-income ratio.
- **🔒 Secure Architecture**: Implements JWT authentication, bcrypt password hashing, input sanitization, and strict API rate-limiting to protect user data and prevent AI abuse.

---

## 🛠️ Tech Stack

### Frontend
- **React + Vite**: Blazing fast modern web framework.
- **TailwindCSS**: For a sleek, responsive, and premium dark-mode UI.
- **Axios**: API interactions with JWT interception.

### Backend
- **FastAPI (Python)**: High-performance asynchronous backend.
- **Google Gemini 2.5 Flash / Pro**: The brain behind Dinero's AI advisor and PDF data structuring.
- **pdfplumber**: Used for high-fidelity extraction of tabular and localized text from PDFs.
- **Supabase (PostgreSQL)**: Scalable, serverless database for secure user and portfolio storage.

---

## 🚀 Deployment (Railway)

Dinero is configured out-of-the-box to be deployed on **Railway** as a monorepo.

### 1. Database Setup
1. Create a project in [Supabase](https://supabase.com).
2. Grab your `DATABASE_URL` (change `postgresql://` to `postgresql+asyncpg://`), `SUPABASE_URL`, and `SUPABASE_ANON_KEY`.

### 2. Backend Deployment
1. Connect this GitHub repo to Railway and create a new service.
2. Railway will automatically detect the `Procfile` and `requirements.txt` and build the Python API.
3. In the Variables tab, add your secrets:
   - `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`
   - `GEMINI_API_KEY`
   - `SECRET_KEY` (Generate a random 64-char hex string)
   - `ALLOWED_ORIGINS` (Set this to your Frontend URL *after* step 3)

### 3. Frontend Deployment
1. Add a **second service** in Railway connected to the exact same GitHub repo.
2. In the Settings tab, change the **Root Directory** to `/frontend/frontend`.
3. In the Variables tab, add:
   - `VITE_API_URL`: Your Backend's public Railway URL (e.g., `https://backend-xyz.up.railway.app/api/v1`).
4. Generate a public domain for the frontend. (Don't forget to put this frontend domain into your Backend's `ALLOWED_ORIGINS` variable!)

---

## 💻 Local Development

1. **Clone the repo**:
   ```bash
   git clone https://github.com/your-username/AI-Money-Mentor.git
   cd AI-Money-Mentor
   ```

2. **Backend Setup**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   
   cp .env.example .env
   # Fill in your GEMINI_API_KEY and other details in .env
   
   python backend/main.py
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend/frontend
   npm install
   
   cp .env.example .env.local
   # Ensure VITE_API_URL=http://localhost:8000/api/v1
   
   npm run dev
   ```

---
*Built with ❤️ for the ET AI Hackathon 2026.*
