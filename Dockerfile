FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/
COPY django_backend /app/django_backend/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV DJANGO_SETTINGS_MODULE=django_backend.settings

CMD ["uvicorn", "django_backend.asgi:application", "--host", "0.0.0.0", "--port", "${PORT:-8000}", "--lifespan", "off"]