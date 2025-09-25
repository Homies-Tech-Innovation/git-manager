# Multi-stage build for better optimization
FROM python:3.10-slim-buster AS builder

# Install uv by copying from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock ./

# Install dependencies only (not the project itself yet)
RUN uv sync --locked --no-install-project

# Copy the rest of the application
COPY src ./src
COPY .env .env

# Install the project itself
RUN uv sync --locked

# Final stage
FROM python:3.10-slim-buster

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY --from=builder /app/src /app/src
COPY --from=builder /app/.env /app/.env

# Set working directory
WORKDIR /app

# Make sure the virtual environment is used
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["python", "-m", "src.main"]