# o42 Marketplace Backend

This is the backend server for the o42 Marketplace application, built with FastAPI.

## Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    -   Rename `.env.example` to `.env`.
    -   Fill in the required values for your databases, API keys, and other settings.

## Running the Server

### Development
For development with live reloading:
```bash
uvicorn app.main:app --reload
```

### Production
For production, use Gunicorn:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

The server will be available at `http://127.0.0.1:8000`.