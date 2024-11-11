FROM python:3.11.6-slim

ENV PYTHONUNBUFFERED = 1

WORKDIR /app

COPY requirements/ requirements/
RUN pip install -r requirements/dev.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]