# CollabFlow

CollabFlow is a FastAPI-based backend service for collaboration workspace management. It provides user authentication, workspace creation, membership management, and workspace listing using an asynchronous SQLAlchemy + MySQL stack.

## Key Features

- User registration and login
- JWT-based authentication and refresh token support
- Create, update, and delete workspaces
- Add members to workspaces with roles
- Get workspace details and list a user’s workspaces
- Health check endpoint and OpenAPI documentation
- Async SQLAlchemy integration with MySQL

## Requirements

- Python 3.11+ (recommended)
- MySQL database
- `venv` or another virtual environment tool

Dependencies are listed in `requirements.txt`.

## Setup

1. Clone the repository.

2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\Activate.ps1  # PowerShell
# or venv\Scripts\activate.bat  # CMD
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your database and application settings.

Example `.env`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=collabflow
DB_USER=your_db_user
DB_PASSWORD=your_db_password

APP_NAME=CollabFlow
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development
ALLOW_DOMAIN=["*"]
LOG_LEVEL=INFO
LOG_FORMAT=%(levelname)s:%(name)s:%(message)s
ENV=development
APP_PORT=8000

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

5. Ensure your MySQL database is running and the configured database exists.

6. Run the application:

```bash
python run.py --host localhost --port 8000 --reload
```

## API Documentation

Once the server is running, API docs are available at:

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Main Endpoints

- `POST /api/v1/user/register` — Register a new user
- `POST /api/v1/user/login` — Login and receive access/refresh tokens
- `POST /api/v1/user/logout` — Logout user using refresh token
- `POST /api/v1/workspace/create-workspace` — Create a workspace
- `GET /api/v1/workspace/workspace-details/{workspace_id}` — Get workspace details
- `PATCH /api/v1/workspace/update-workspace/{workspace_id}` — Update workspace
- `POST /api/v1/workspace/add-member/{workspace_id}` — Add a member to a workspace
- `GET /api/v1/workspace/get-user-workspaces/{user_id}` — List workspaces for a user
- `DELETE /api/v1/workspace/{workspace_id}` — Soft delete a workspace
- `GET /health` — System health check

## Project Structure

- `app/app.py` — FastAPI application setup
- `app/api/v1/endpoints/` — API route handlers
- `app/config/config.py` — application settings and environment config
- `app/core/database.py` — async SQLAlchemy engine and database session
- `app/models/` — database models
- `app/schemas/` — request/response data models
- `app/services/` — business logic and service layer
- `app/repositories/` — database access layer

## Notes

- This project uses asynchronous SQLAlchemy with a MySQL backend.
- The application expects environment variables from `.env` to configure the database and security settings.
- Adjust `run.py` host/port options as needed for deployment.


