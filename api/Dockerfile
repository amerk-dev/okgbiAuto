FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

# Установка системных библиотек, необходимых для WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libxml2 \
    libxslt1.1 \
    fonts-liberation \
    shared-mime-info \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода проекта
COPY . .
COPY ./entrypoint.sh /code/entrypoint.sh
# Make entrypoint script executable
RUN chmod +x /code/entrypoint.sh

# Сбор статики, если требуется
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# CMD is overridden by entrypoint in docker-compose.yml
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout 3000", "okgbi.wsgi:application"]
