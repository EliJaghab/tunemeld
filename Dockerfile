FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

WORKDIR /app

# Copy pyproject.toml first for better Docker layer caching
COPY pyproject.toml /app/pyproject.toml

# Install Python dependencies
RUN pip install --upgrade pip && pip install -e .

# Copy Django backend files to container
COPY django_backend/ /app/

# Debug: List files to verify copy worked
RUN echo "=== VERIFYING FILE COPY ===" && \
    ls -la /app/ && \
    echo "=== CHECKING FOR MANAGE.PY ===" && \
    ls -la /app/manage.py && \
    echo "=== COPY VERIFICATION COMPLETE ==="

# Set Python path for Django
ENV PYTHONPATH=/app

# Expose port 8080 (matches Railway configuration)
EXPOSE 8080

# Start Django server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "core.wsgi:application"]
