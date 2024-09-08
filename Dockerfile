FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY django_backend /app/django_backend/
COPY entrypoint.sh /app/

ENV DJANGO_SETTINGS_MODULE=django_backend.settings

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]