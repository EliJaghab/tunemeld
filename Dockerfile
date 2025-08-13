FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

WORKDIR /app

# Copy Django backend files to container
COPY django_backend/ /app/

# Debug: List files to verify copy worked
RUN echo "=== VERIFYING FILE COPY ===" && \
    ls -la /app/ && \
    echo "=== CHECKING FOR MANAGE.PY ===" && \
    ls -la /app/manage.py && \
    echo "=== COPY VERIFICATION COMPLETE ==="

# Install Python dependencies including gunicorn
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install gunicorn

# Set Python path for Django
ENV PYTHONPATH=/app

# Expose port 8000
EXPOSE 8000
