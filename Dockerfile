FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies including gunicorn
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install gunicorn

# Copy Django backend files to container
COPY django_backend/ /app/

# Copy playlist_etl module (required by Django models)
COPY playlist_etl/ /app/playlist_etl/

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
