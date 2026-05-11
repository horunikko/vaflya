FROM python:3.12-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Сначала копируем зависимости
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "app/start.py"]