# AI-Based Retinal Image Classification for Early Detection of Eye Diseases

Full-stack clinical decision-support prototype combining **React.js**, **Pure Flask + Flask-SocketIO**, **TensorFlow / Keras**, and **MongoDB** across three role-based portals (**Patient**, **Doctor**, **Admin**).

> **Clinical Disclaimer:** This application is an educational and clinical decision-support prototype, not a replacement for a comprehensive eye examination or diagnosis by a qualified healthcare professional.

## Classification Categories

1. `Normal`
2. `Glaucoma`
3. `Hypertensive Retinopathy`
4. `Diabetic Retinopathy`

## Backend Setup (`backend/`)

```bash
cd backend
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env` and set `MONGO_URI`, `SECRET_KEY`, and `JWT_SECRET_KEY`.

Provision the administrator account (password >= 16 characters):

```bash
python scripts/create_admin.py
```

Configure the trained Keras model (`backend/ai_model/retinal_model.keras` and `backend/ai_model/preprocessing.json` from `preprocessing.example.json`), or train one using `python ai_model/train_model.py` after installing `requirements-ai.txt`.

Start the Flask + Socket.IO server:

```bash
python app.py
```

Run backend tests:

```bash
pytest
```

## Frontend Setup (`frontend/`)

```bash
cd frontend
npm install
npm run dev
```

Build for production:

```bash
npm run build
```
