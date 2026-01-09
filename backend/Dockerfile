# Backend Dockerfile for EUFSI LCA Tool - Optimized for Render
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for scientific Python packages
# Combine commands to reduce layers and use --no-install-recommends
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    gfortran \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    libopenblas-dev \
    liblapack-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install wheel for faster builds
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install critical dependencies first (for faster startup if build partially fails)
RUN pip install --no-cache-dir \
    fastapi==0.110.1 \
    uvicorn==0.25.0 \
    motor==3.3.1 \
    pymongo==4.5.0 \
    pydantic==2.12.5 \
    pydantic-settings==2.12.0 \
    python-dotenv==1.2.1 \
    python-jose==3.5.0 \
    passlib==1.7.4 \
    bcrypt==4.1.3 \
    python-multipart==0.0.21 \
    email-validator==2.3.0 \
    reportlab==4.4.7

# Install remaining dependencies (this may take time)
# Continue even if some optional packages fail
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy the rest of the application
COPY . .

# Create directory for Brightway2 data
RUN mkdir -p /tmp/lca_projects

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application (production mode, no reload)
# Use shell form to allow environment variable substitution
CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
