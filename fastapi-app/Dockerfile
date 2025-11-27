# ======= Stage 1: builder =======
FROM python:3.12-slim AS builder

# Base env for Python correctness
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Only runtime-dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ======= Stage 2: runtime =======
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed packs from builder-image
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy in app source code
COPY app ./app

# Create a non-root user to run app
RUN useradd -m appuser
USER appuser

EXPOSE 8000

# Start FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
