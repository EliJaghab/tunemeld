FROM python:3.12-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml .

# Install dependencies
RUN pip install -e .

# Copy application code
COPY . .

# Set environment variables for local testing
ENV PYTHONPATH=/app/backend:/app
ENV DJANGO_SETTINGS_MODULE=core.settings

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
