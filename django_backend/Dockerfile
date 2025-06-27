FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1

WORKDIR /

COPY . /

ENV PYTHONPATH=/

RUN pip install --upgrade pip && pip install -r /requirements.txt

EXPOSE 8000
EXPOSE 5678

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
