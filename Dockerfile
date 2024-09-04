FROM python:3.10-slim

WORKDIR /app

COPY . /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV DJANGO_SETTINGS_MODULE=django_backend.settings

CMD ["uvicorn", "django_backend.asgi:application", "--host", "0.0.0.0", "--port", "8000"]