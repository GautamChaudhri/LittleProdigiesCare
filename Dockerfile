FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create directory for the SQLite database
RUN mkdir -p /app/data

EXPOSE 8000

# Run with gunicorn — 2 workers is plenty for a small site
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--chdir", "backend", "app:app"]
