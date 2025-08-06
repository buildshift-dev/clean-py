FROM python:3.12-slim
# there maybe known vulnerabilties, but this is ok for a public demo

WORKDIR /app

# Install system dependencies and security updates
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY pyproject.toml ./

# Install the application in development mode
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment variables for local development
ENV API_BASE_URL=http://localhost:8000

# Default command runs both FastAPI and Streamlit
CMD ["sh", "-c", "uvicorn src.presentation.main:app --host 0.0.0.0 --port 8000 & streamlit run src/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --server.runOnSave true --server.allowRunOnSave true"]
