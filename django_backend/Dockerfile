FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1

WORKDIR /app

COPY . .

ENV PYTHONPATH=/app

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8000

# Debug: List files to verify they were copied
RUN ls -la /app/ && echo "Django files copied successfully"

CMD ["python3", "startup_debug.py"]
