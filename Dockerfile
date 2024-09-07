FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/
COPY django_backend /app/django_backend/
COPY entrypoint.sh /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV DJANGO_SETTINGS_MODULE=django_backend.settings

ENTRYPOINT ["./entrypoint.sh"]