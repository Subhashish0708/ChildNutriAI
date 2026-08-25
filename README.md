# ChildNutri AI: Malnourishment Identification in Infants using AI

An intelligent AI-powered pediatric health platform for identifying, tracking, and managing malnutrition (Stunting, Wasting, Underweight, Severe Acute Malnutrition) in infants.

---

## 🏗️ Project Architecture

```
ChildNutri-AI/
├── frontend/                     # Pure HTML, CSS, JavaScript (Untouched UI)
│   ├── index.html                # Landing Page + Login / Register Modal
│   ├── dashboard.html            # Health Worker Dashboard UI
│   ├── dashboard.css             # Health Worker Styling
│   ├── dashboard.js              # Health Worker API Connector
│   ├── parent_dashboard.html     # Parent / Guardian Dashboard UI
│   ├── parent_dashboard.css      # Parent Dashboard Styling
│   └── parent_dashboard.js       # Parent API Connector
│
├── backend/                      # FastAPI Python Application
│   ├── main.py                   # App Entry, CORS, Static Files, Routers
│   ├── database.py               # SQLite Engine & Session Configuration
│   ├── models.py                 # SQLAlchemy Database Models
│   ├── schemas.py                # Pydantic Request/Response Schemas
│   ├── dependencies.py           # JWT Authentication & Role Authorization
│   ├── routers/                  # Modular API Route Controllers
│   │   ├── auth.py               # /api/auth (Register, Login, Me, Logout)
│   │   ├── users.py              # /api/users (Live Dashboard Analytics)
│   │   ├── children.py           # /api/children (CRUD & Growth History)
│   │   ├── assessments.py        # /api/assessments (AI Assessment Pipeline)
│   │   ├── photos.py             # /api/photos (Multipart Upload & Gallery)
│   │   ├── medical.py            # /api/medical (Clinical History Timeline)
│   │   ├── nutrition.py          # /api/nutrition (Diet & RUTF Plans)
│   │   ├── appointments.py       # /api/appointments (Scheduling & Status)
│   │   ├── notifications.py      # /api/notifications (Alerts & Badges)
│   │   └── ai.py                 # /api/ai (Direct Inference Endpoints)
│   └── services/
│       ├── auth_service.py       # bcrypt hashing & JWT token handling
│       ├── ai_service.py         # WHO Z-score engine & ML model hook
│       └── image_service.py      # Secure image uploads to disk
│
├── database/
│   └── childnutri.db             # Operational SQLite Database
│
├── uploads/
│   └── children/                 # Uploaded child photos (on disk, not DB BLOB)
│
├── dataset/                      # Separated AI Training Datasets
│   ├── anthropometric_data.csv   # Training dataset for AI models
│   └── image_labels.csv          # Visual classification tags
│
├── ai/                           # AI Model Training & Inference Scripts
│   ├── train.py                  # Standalone ML training script
│   ├── predict.py                # Standalone test inference script
│   └── models/                   # Serialized ML models (.pkl / .h5)
│
├── seed.py                       # Development Database Seeder
├── requirements.txt              # Python Dependencies
├── .env.example                  # Environment Configuration Template
└── README.md
```

---

## 🚀 Quick Setup (Windows)

### 1. Create Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```powershell
python seed.py
```

### 4. Start the FastAPI Backend Server
```powershell
uvicorn backend.main:app --reload --port 8000
```
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

### 5. Launch the Frontend
Open `frontend/index.html` directly in your browser, or serve it using VS Code Live Server / Python HTTP Server:
```powershell
# In another terminal window:
cd frontend
python -m http.server 5500
```
Visit `http://127.0.0.1:5500/index.html` in your browser.

---

## 🔑 Demo Login Credentials (from seed.py)

| Role | Email | Password | Target Dashboard |
|---|---|---|---|
| **Parent / Guardian** | `priya.sharma@email.com` | `Parent@123` | `parent_dashboard.html` |
| **Health Worker** | `dr.subha@childnutri.org` | `Doctor@123` | `dashboard.html` |
| **Pediatrician** | `dr.meena@childnutri.org` | `Doctor@123` | `dashboard.html` |

---

## 🤖 AI Model Workflow

1. **Training Separation**: Training CSV data in `dataset/` is used by `ai/train.py` to train models.
2. **Model Storage**: Trained artifacts are saved into `ai/models/`.
3. **Inference Pipeline**: `backend/services/ai_service.py` executes AI inference on assessment data and returns classification (`Normal`, `Stunted`, `Wasted`, `Underweight`, `Severe (SAM)`), risk score (0-100), and confidence.
