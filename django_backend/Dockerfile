FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1

WORKDIR /app

COPY . /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN chmod +x /django_backend/manage.py

EXPOSE 8000
EXPOSE 5678

CMD ["python3", "django_backend/manage.py", "runserver", "0.0.0.0:8000"]