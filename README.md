# Multi-Modal Medical Diagnosis Assistant

A production-grade, real full-stack clinical decision support application powered by PyTorch DenseNet-121 deep learning models, multimodal late-fusion neural networks, and Grad-CAM visual explainability.

> [!NOTE]
> **Research & Educational Demonstration Notice**: This application is a machine-learning research and educational demonstration. It is not an FDA-approved or CE-certified medical device and must not be used as a substitute for diagnosis, evaluation, or treatment by a licensed physician or healthcare professional.

---

## 1. System Architecture

The application implements a decoupled, modern clinical full-stack architecture:

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React + Vite + TypeScript)"]
        UI["Clinical Interface (Tailwind CSS)"]
        AC["AuthContext (JWT Bearer Storage)"]
        DiagPage["Multimodal Diagnostic Workspace"]
        HistPage["Paginated History & Audit Logs"]
        DashPage["Live Dashboard (DB Calculated Stats)"]
    end

    subgraph API["FastAPI Application Server (Python 3.11+)"]
        AuthRouter["/api/auth (Bcrypt + PyJWT)"]
        DiagRouter["/api/diagnosis (Validation & Pipeline)"]
        FileRouter["/api/files (Path-Traversal Guarded File Streaming)"]
        HealthRouter["/api/health (Live DB & Model Readiness)"]
    end

    subgraph Services["Core Application Services"]
        DiagService["DiagnosisService (Audit & Transactions)"]
        FileService["FileService (UUID Storage & Sanitization)"]
        ModelMgr["ModelManager (Resident Eval Models in Memory)"]
    end

    subgraph ML["PyTorch Diagnostic Engine"]
        DenseNet["DenseNet-121 Transfer Learning"]
        SymptomMLP["Symptom Encoder MLP (8 Features)"]
        Fusion["Late-Fusion Head (Image Emb + Symptom Emb)"]
        GradCAM["Grad-CAM (Conv2 Feature Maps)"]
    end

    subgraph Persistence["Storage & Database"]
        Postgres[("PostgreSQL 16 (or SQLite Fallback)")]
        DiskStorage["backend/storage/{uploads, gradcam}"]
    end

    UI --> DiagRouter
    UI --> AuthRouter
    UI --> FileRouter
    UI --> HealthRouter

    DiagRouter --> DiagService
    DiagService --> ModelMgr
    ModelMgr --> DenseNet
    ModelMgr --> SymptomMLP
    ModelMgr --> Fusion
    ModelMgr --> GradCAM
    DiagService --> FileService
    DiagService --> Postgres
    FileService --> DiskStorage
```

---

## 2. Key Capabilities & Engineering Standards

* **Zero Demo/Seed Data**: The application starts with an **empty database**. No fabricated patients, demo doctors, or simulated history records. A newly registered user sees 0 diagnoses, 0 statistics, and an authentic empty-state UI.
* **Real PyTorch Neural Inference**: No randomized predictions or artificial confidence scores. Real `.pth` checkpoints run DenseNet-121 image classification and Late-Fusion multimodal inference.
* **Visual Explainability (Grad-CAM)**: Visual attention heatmaps are dynamically generated via backpropagation on the last convolutional layer of DenseNet-121 (`model.features.denseblock4.denselayer16.conv2`) and blended with the original radiograph.
* **Strict Clinical Data Isolation**: Doctor records are isolated at the database query level via authenticated JWT identity. User A cannot view, query, or delete User B's audit trail.
* **Secure File Handling**: Uploaded clinical scans and Grad-CAM overlays are stored using cryptographically secure UUID filenames with path-traversal prevention.
* **Alembic Migrations**: Full schema evolution supporting PostgreSQL and local SQLite fallback.

---

## 3. Technology Stack

### Backend
* **Language**: Python 3.11+ (Tested on Python 3.13)
* **Framework**: FastAPI & Uvicorn
* **Database & ORM**: SQLAlchemy 2.x & PostgreSQL (or SQLite local fallback)
* **Migrations**: Alembic 1.13+
* **Validation**: Pydantic v2 & Pydantic-Settings
* **Security**: Direct `bcrypt` password hashing & `PyJWT` bearer tokens
* **Machine Learning**: PyTorch 2.x, Torchvision, Pillow, NumPy, Matplotlib

### Frontend
* **Build Tool**: Vite 5.x
* **Framework**: React 18+ with TypeScript
* **Styling**: Tailwind CSS (Clinical slate and navy theme)
* **Icons**: Lucide React
* **Routing**: React Router DOM 6+ (Protected route guards)

### Containerization & Deployment
* **Docker Compose**: Orchestrates `postgres:16-alpine`, `backend`, and `frontend` (Nginx).

---

## 4. Local Installation & Setup

### Prerequisites
* Python 3.11+
* Node.js 18+ and `npm`
* PostgreSQL 14+ (Optional; SQLite is configured as an immediate out-of-the-box local fallback)

### Step 1: Clone Repository
```bash
git clone https://github.com/example/medical-diagnosis-assistant.git
cd medical-diagnosis-assistant
```

### Step 2: Backend Setup
```bash
# Create and activate Python virtual environment
python -m venv .venv

# Windows (Command Prompt / PowerShell):
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 3: Configure Environment Variables
Copy the example environment files:
```bash
# Windows:
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env

# Linux / macOS:
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

To use PostgreSQL, configure `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/medical_assistant
JWT_SECRET_KEY=generate_a_secure_random_key_min32_chars
MODEL_DEVICE=cpu
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```
*Note: If no PostgreSQL server is running, the default fallback is `sqlite:///../data/app.db`.*

### Step 4: Run Database Migrations
```bash
cd backend
alembic upgrade head
cd ..
```

### Step 5: Frontend Setup
```bash
cd frontend
npm install
npm run build   # Validates TypeScript types and generates production bundle
cd ..
```

---

## 5. Running the Application Locally

You can launch the full stack using the provided batch scripts (Windows) or terminal commands:

### Option A: Using Batch Scripts (Windows)
* Double-click `run_backend.bat` (launches FastAPI at `http://127.0.0.1:8000`)
* Double-click `run_frontend.bat` (launches Vite frontend at `http://localhost:5173`)

### Option B: Using Terminal Commands

**Terminal 1 (Backend):**
```bash
# Activate virtual environment
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/macOS

uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Open your browser to: **`http://localhost:5173`**

---

## 6. Docker Compose Deployment

To run the complete production-style environment with PostgreSQL, FastAPI, and Nginx-served React:

```bash
docker compose up --build
```

Services started:
* **PostgreSQL Database**: `postgres:5432` with persistent volume `postgres_data`
* **FastAPI Backend**: `http://localhost:8000` with persistent volume `storage_data`
* **React SPA (Nginx)**: `http://localhost:5173`

---

## 7. Machine Learning Architecture & Checkpoints

The system incorporates two multimodal diagnostic pipelines:

### Modality 1: Chest X-Ray
* **Classes (5)**: `Atelectasis`, `Cardiomegaly`, `Consolidation`, `Edema`, `Pleural Effusion`
* **Backbone**: DenseNet-121 (Features: 1024-dim embedding)
* **Symptom Vector (8-dim boolean features)**:
  `cough`, `fever`, `dyspnea`, `chest_pain`, `fatigue`, `hemoptysis`, `wheezing`, `tachypnea`
* **Late-Fusion**: Concatenates DenseNet 1024-dim visual embedding with SymptomMLP 16-dim embedding (1040-dim total) -> 128-dim hidden layer with ReLU and Dropout (0.2) -> 5-class logits.
* **Checkpoint paths**:
  - `models/chest_xray/densenet121_chest.pth`
  - `models/chest_xray/fusion_chest.pth`

### Modality 2: Brain MRI
* **Classes (4)**: `Glioma`, `Meningioma`, `No Tumor`, `Pituitary`
* **Backbone**: DenseNet-121 (Features: 1024-dim embedding)
* **Symptom Vector (8-dim boolean features)**:
  `headache`, `seizures`, `vision_changes`, `nausea_vomiting`, `cognitive_decline`, `balance_issues`, `motor_weakness`, `speech_difficulty`
* **Late-Fusion**: Concatenates DenseNet 1024-dim visual embedding with SymptomMLP 16-dim embedding (1040-dim total) -> 128-dim hidden layer -> 4-class logits.
* **Checkpoint paths**:
  - `models/brain_mri/densenet121_brain.pth`
  - `models/brain_mri/fusion_brain.pth`

---

## 8. ML Training / Checkpoint Regeneration

> [!IMPORTANT]
> The web application **never** retrains models on startup. The training scripts below are provided for standalone offline execution or retraining on new clinical benchmarks.

### Standalone Checkpoint Bootstrapper
If checkpoint weights are missing on disk, they can be initialized using:
```bash
python -m backend.app.ml.weights_init
```

### Full Retraining Pipeline (Offline)
1. **Dataset Preparation**:
   - Organize imaging datasets into `data/train/` and `data/val/` directories sorted by class name.
   - For multimodal fusion training, pair images with corresponding JSON symptom metadata.
2. **Preprocessing**:
   - Resize to $(224 \times 224)$.
   - Normalize using ImageNet statistics ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$).
3. **Training Image Backbone**:
   - Optimizer: AdamW ($lr = 10^{-4}$, weight decay $10^{-2}$).
   - Loss: CrossEntropyLoss with class weighting.
4. **Training Late-Fusion Head**:
   - Freeze DenseNet-121 convolutional backbone.
   - Train SymptomMLP and Fusion classifier head for 25 epochs.
5. **Output**:
   - Save weights via `torch.save(model.state_dict(), path)`.

---

## 9. API Reference

### Authentication
* `POST /api/auth/register` — Register new clinician account
* `POST /api/auth/login` — Authenticate and receive JWT bearer token
* `GET /api/auth/me` — Retrieve current authenticated clinician profile

### Diagnosis & Inference
* `POST /api/diagnosis/infer` — Execute multimodal inference with image upload and symptom flags
* `GET /api/diagnosis/metadata` — Clinical classes and symptom checklists
* `GET /api/diagnosis/history?page=1&page_size=10` — Paginated history for authenticated user
* `GET /api/diagnosis/history/{id}` — Retrieve specific record details
* `DELETE /api/diagnosis/history/{id}` — Delete audit record and associated image files
* `GET /api/diagnosis/stats` — Real calculated dashboard metrics

### File Storage
* `GET /api/files/{category}/{filename}` — Safely retrieve scan or Grad-CAM overlay

### System Health
* `GET /api/health` — Live check on database and PyTorch model readiness

---

## 10. Automated Test Suite

A comprehensive test suite using `pytest` and `FastAPI TestClient` is included:

```bash
# Run all tests
pytest backend/tests -v
```

Tests verify:
1. **Authentication**: Registration, email conflict rejection, invalid credentials, JWT encoding/decoding.
2. **Database Isolation**: Confirms Doctor 2 cannot see Doctor 1's history or statistics.
3. **Empty States**: Confirms 0 records produce genuine zero metrics.
4. **Validation**: Unsupported file extensions, empty payloads, and invalid modalities.
5. **Machine Learning**: ModelManager residency, image preprocessing, DenseNet-121 inference, and Grad-CAM generation.
6. **Deletion**: Verified ownership and cascade removal of physical files.

---

## 11. Security Governance

* **Password Protection**: Salted bcrypt hashing with 12 rounds.
* **Token Security**: Signed HS256 JWT tokens with configurable expiration timestamps.
* **Path Traversal Defense**: File storage routes strictly verify directory containment before streaming.
* **No Information Leakage**: Database models containing password hashes are never serialized directly to clients.
