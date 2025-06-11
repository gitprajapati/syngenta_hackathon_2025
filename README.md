# Syngenta Hackathon 2025

This repository contains a full stack project developed for the Syngenta Hackathon 2025. The backend exposes a FastAPI service with RAG (Retrieval Augmented Generation) capabilities and the frontend is a Vue 3 application.

## Project Structure

- **backend/** – FastAPI service and machine learning utilities.
- **frontend/** – Vue 3 web client.

## Prerequisites

- Python 3.10+
- Node.js 16+

## Backend Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Optional: create a `.env` file to override settings in `core/config.py`
uvicorn main:app --reload
```

The service will start on `http://localhost:8000` with automatically generated Swagger docs available at `/docs`.

## Frontend Setup

```bash
cd frontend
npm install
npm run serve
```

The default development server runs on `http://localhost:8080` and proxies API requests to the backend.

## License

This project is provided for hackathon use. See individual source files for license information.
