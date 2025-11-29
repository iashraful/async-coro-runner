FROM python:3.13-slim AS builder
WORKDIR /api

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc g++ python3-dev libssl-dev libffi-dev zlib1g-dev libjpeg-dev && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install poetry
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

# Configure poetry to avoid creating virtual environments

# Copy only dependency files for caching
COPY pyproject.toml uv.lock /api/
# Install dependencies without root project
RUN uv pip install --no-cache --system -r pyproject.toml

# Final stage
FROM python:3.13-slim
WORKDIR /api
ENV UV_LINK_MODE=copy
# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-traditional libjpeg-dev zlib1g-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . /api/
