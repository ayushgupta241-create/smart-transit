"""WSGI entry point used by gunicorn inside the container."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Local development only; the container runs gunicorn instead.
    app.run(host="127.0.0.1", port=8000)
