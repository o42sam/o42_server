# o42 Backend

Backend for the o42 e-commerce platform.

## Setup

1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Set up `.env` file with credentials (see `.env` sample above).
4. Run MongoDB locally or update `MONGODB_URI`.
5. Start Redis for Celery: `redis-server`
6. Run the app: `poetry run uvicorn app.main:app --reload`
7. For production: `poetry run gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`

## Features

- User management (agents and customers)
- Order processing with NLP matching
- Photo verification with face recognition
- Email and SMS notifications
- Secure JWT authentication