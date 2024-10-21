# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем необходимые пакеты для работы с PostgreSQL
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию внутри контейнера
WORKDIR /usr/src/app

# Копируем файл зависимостей в контейнер
COPY req.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r req.txt

# Копируем весь проект в контейнер
COPY . .

# Открываем порт 8000 для доступа
EXPOSE 8000

# Запускаем сервер Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
