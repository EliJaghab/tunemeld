FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYDEVD_DISABLE_FILE_VALIDATION=1

WORKDIR /

COPY . /

ENV PYTHONPATH=/

RUN pip install --upgrade pip && pip install -r /requirements.txt

# Debug: List files to verify manage.py is copied correctly
RUN ls -la /

# Verify manage.py exists and is executable (remove redundant chmod)
RUN test -f manage.py && echo "manage.py found" || echo "manage.py NOT found"

EXPOSE 8000
EXPOSE 5678

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
