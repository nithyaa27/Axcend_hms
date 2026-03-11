# HMS Role-Based Platform (Patient Module)

This repository currently contains the **Patient module** of HMS:
- `backend/`: Flask API and data models
- `frontend/`: Vue UI for patient workflows

The codebase is prepared for integration with Doctor and Admin modules without changing patient business logic.

## 1. Quick Start

### Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173` and proxies `/api` to backend.

## 2. Production-Safe Config

Backend uses environment variables (see `backend/.env.example`):
- `HMS_SECRET_KEY`
- `HMS_DATABASE_URI`
- `HMS_CORS_ORIGINS`
- `HMS_SESSION_SECURE`
- `HMS_SESSION_SAMESITE`
- `FLASK_DEBUG`
- `HMS_FRONTEND_URL`
- `HMS_SMTP_HOST`
- `HMS_SMTP_PORT`
- `HMS_SMTP_USER` (default: `hmsproject26@gmail.com`)
- `HMS_SMTP_APP_PASSWORD` (16-character Gmail app password)

Frontend build:
```powershell
cd frontend
npm run build
```

## 3. Integration Handover

Use the detailed merge document:
- `docs/HMS_Merge_Handover.md`
- `docs/HMS_Merge_Handover.pdf`

These files define module boundaries, API contracts, role routing expectations, and merge checklist for Doctor/Admin integration.

