FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for image processing and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy project files
COPY backend ./backend
COPY models ./models
COPY data ./data

ENV PYTHONPATH=/app
ENV MODEL_DEVICE=cpu

EXPOSE 8000

# Run migrations and start uvicorn
CMD ["sh", "-c", "cd backend && alembic upgrade head && cd /app && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
