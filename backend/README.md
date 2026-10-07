# MPLADS Sentinel AI — Backend API (SIH Prototype)

FastAPI backend service providing database models, health status, and project data endpoints for the MPLADS Sentinel AI decision support prototype.

## Setup Instructions (Windows PowerShell)

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Seed controlled prototype test database (12 sample records)
python seed.py

# 6. Run FastAPI backend server
uvicorn app.main:app --reload --port 8000
```

## Available Endpoints

- **Health Status**: `GET http://localhost:8000/health`
- **List All Projects**: `GET http://localhost:8000/api/projects`
- **Total Project Count**: `GET http://localhost:8000/api/projects/count`
- **Get Project by ID**: `GET http://localhost:8000/api/projects/{project_id}`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
