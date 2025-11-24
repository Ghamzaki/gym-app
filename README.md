# 🛡️ FastAPI RBAC API (Supabase & Render Deployment)

This project is a secure backend API built with FastAPI, demonstrating Role-Based Access Control (RBAC) using JWTs (JSON Web Tokens).

Data persistence is managed by a PostgreSQL database hosted on **Supabase**. The application server itself is hosted on **Render**.

## 🚀 Setup and Run Locally

### 1. Prerequisites

* Python 3.10+
* A Supabase Project (to get your PostgreSQL connection URI)
* A Git repository (for Render deployment)

### 2. Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## 2. Deployment Configuration (`render.yaml`) 🚀

This file instructs Render on how to build and run the service.

```yaml
# render.yaml
# Defines the infrastructure for your FastAPI Service on Render

services:
  - type: web
    name: gym-rbac-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    # This command is crucial: it tells Render to run the 'app' instance inside 'app/main.py'
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    
    # Environment variables are defined here but set securely in the Render dashboard.
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.x
      - key: DATABASE_URL # Set securely in the dashboard
        sync: false
      - key: JWT_SECRET_KEY # Set securely in the dashboard
        sync: false