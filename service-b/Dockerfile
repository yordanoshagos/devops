FROM python:3.11.9-slim-bookworm

WORKDIR /app

# Install curl for health checks and debugging
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN useradd --system --create-home appuser
USER appuser

EXPOSE 3002

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -sf http://localhost:3002/health || exit 1

CMD ["python", "app.py"]
