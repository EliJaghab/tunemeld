# Use GitHub Container Registry Python 3.13 image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

WORKDIR /app

# Copy pyproject.toml first for better Docker layer caching
COPY pyproject.toml /app/pyproject.toml

# Install Python dependencies using uv (faster than pip)
RUN uv pip install --system --upgrade pip && uv pip install --system -e .

# Copy Django backend files to container
COPY backend/ /app/

# Copy .github directory for workflow configuration
COPY .github/ /app/.github/

# Set Python path for Django
ENV PYTHONPATH=/app

# Expose port 8080
EXPOSE 8080

# Start Django server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "core.wsgi:application"]
