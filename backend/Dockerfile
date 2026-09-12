FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=factorai_config.settings.production

WORKDIR /app

# psycopg[binary] ships prebuilt wheels, so no postgres dev headers needed.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "factorai_config.wsgi:application", "--bind", "0.0.0.0:8000"]
