# ── BUILDER STAGE ──
FROM python:3.11-slim as builder

WORKDIR /app

# Install only essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create wheels for all dependencies (this pre-compiles them)
RUN pip install --user --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir --no-warn-script-location \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# ── RUNTIME STAGE ──
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built packages from builder
COPY --from=builder /root/.local /root/.local

# Set PATH for user-installed packages
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY . .

# Ensure .streamlit config is used
ENV STREAMLIT_CONFIG_DIR=/app/.streamlit

# Expose port
EXPOSE 8080

# Run the app
CMD ["streamlit", "run", "router.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]