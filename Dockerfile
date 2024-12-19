FROM python:3.9-slim

# Встановлення залежностей
WORKDIR /app
COPY . /app
RUN pip install pymongo

# Опис команди запуску
CMD ["python", "main.py"]
