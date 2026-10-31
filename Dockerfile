FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DATA_DIR=/data

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN DJANGO_SECRET_KEY=build-only DJANGO_DEBUG=False python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["sh", "/app/deploy/start.sh"]