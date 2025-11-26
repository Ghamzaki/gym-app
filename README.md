# Gym Management API Built with FastAPI

**A robust RESTful API built with FastAPI and SQLAlchemy to manage users, memberships, and services for a modern gym or fitness center.**

This project is a secure backend API built with FastAPI, demonstrating Role-Based Access Control (RBAC) using JWTs (JSON Web Tokens).

Data persistence is managed by a PostgreSQL database hosted on **render**. The application server itself is hosted on **Render**.

## 📋 Table of Contents

1.  [🌟 Features](#-features)
2.  [🚀 Getting Started](#-getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
    * [Running the Application](#running-the-application)
3.  [🧭 API Endpoints (Swagger UI)](#-api-endpoints-swagger-ui)
    * [Authentication Flow](#authentication-flow)
    * [Key Routes](#key-routes)
4.  [🧪 Testing](#-testing)
5.  [🏗️ Project Structure](#-project-structure)
6.  [🤝 Contribution](#-contribution)
7.  [📄 License](#-license)
8.  [📧 Contact](#-contact)

## 🌟 Features

* **User Management:** Secure registration, login, and profile retrieval.
* **Role-Based Access Control (RBAC):** Differentiates access for `member`, `trainer`, and `admin` roles.
* **Authentication:** Secure **JWT (JSON Web Token)** based authentication.
* **Service Catalog:** Endpoints to view available gym services.
* **Database:** Persistent data storage using **SQLAlchemy ORM** with a SQLite backend for development.

---

## 🚀 Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* You will need **Python 3.10+** and `pip`.
* A Render Project (to get your PostgreSQL connection URI)
* A Git repository (for Render deployment)

```bash
# Check your Python version
python3 --version

### 🚀 Setup and Run Locally

## 1. Clone the Repository
```bash
git clone [Your Repository URL]
cd gym-app

## 2. Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
# .\venv\Scripts\activate # On Windows
pip install -r requirements.txt

## 3. Running the Application
uvicorn app.main:app --reload

### Deployment Configuration (`render.yaml`) 🚀
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

### API Endpoints (Swagger UI)

The interactive API documentation is available automatically when the server is running, powered by Swagger UI. This is the primary interface for testing endpoints and viewing schemas.
### Documentation URL
http://127.0.0.1:8000/docs

### Authentication Flow
All protected routes require a JWT. Follow these steps in the Swagger UI to authenticate:
## 1. Login:
Use the POST /token route to submit credentials (username = email, password) and receive the JWT access_token.
## 2. Authorize:
Click the "Authorize" button at the top of the /docs page. In the value field, enter the token in the format: Bearer [your_access_token].

### Key Routes
Method          Path                Description                                         Access 
POST        /register       Create a new user account.                              Public
POST        /token          Exchange credentials for an Access Token (Login).       Public
GET         /users/me       Retrieve the profile of the current authenticated user. Membe+
GET         /services       View the list of all available gym services.            Member+
PATCH       /admin/update-role/{user_id}    Change a user's role.                  AdminOnly

### Testing
The project uses Pytest for unit and integration testing.

## 1. Install testing dependencies:
```Bash
pip install pytest pytest-asyncio httpx

## 2. Run all tests:
```Bash
pytest

### Project Structure

gym-app/
├── app/
│   ├── main.py             # FastAPI application and top-level routing
│   ├── auth.py             # Security logic (JWT creation, password hashing)
│   ├── crud.py             # Database operations (Create, Read, Update, Delete)
│   ├── database.py         # SQLAlchemy engine and session management
│   ├── models.py           # SQLAlchemy declarative base models
│   ├── schemas.py          # Pydantic models for request/response validation
│   ├── test_api.py         # Integration and feature tests
│   └── conftest.py         # Pytest fixtures (DB setup, test client)
├── requirements.txt        # Project dependencies
├── pytest.ini              # Pytest configuration file
└── README.md               # Project documentation

### Contribution
Ccontributors are welcome! Please follow these steps:
* Fork the repository.
* Create a new feature branch (git checkout -b feature/your-feature-name).
* Commit your changes (git commit -m 'feat: Add new user profile field').
* Push to the branch (git push origin feature/your-feature-name).
* Open a Pull Request describing your changes.

### License
This project is licensed under the [GMK License]

### Contact:
- [Name: Usman Ghamzaki Abdulhamid/GitHub Handle: Ghamzaki]
- [X handle: @__Ghamzaki]
- [Email: uthmanghamzaki@gmail.com]
- Project Link: [https://github.com/Ghamzaki/gym-app.git]