FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1

WORKDIR /

COPY django_backend/ /

ENV PYTHONPATH=/

RUN pip install --upgrade pip && pip install -r /requirements.txt

RUN chmod +x /manage.py

EXPOSE 8080
EXPOSE 5678

CMD ["python3", "/manage.py", "runserver", "0.0.0.0:8080"]
