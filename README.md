# Python Bash

## Установка и сборка

### 1. Сборка Docker-образа
Для создания Docker-образа выполните:
```bash
docker build -t ebash .
```
*Совет:* Добавьте `--no-cache` для чистой сборки, если возникают проблемы:
```bash
docker build -t ebash . --no-cache
```

## Запуск приложения

### 2. Основной запуск
Для запуска основного приложения:
```bash
docker run -it ebash
```

## Тестирование

### 3. Запуск тестов
Для выполнения всех тестов:
```bash
docker run -it ebash pytest src/tests/
```

### 4. Запуск конкретного теста
Для запуска определенного тест-файла:
```bash
docker run -it ebash pytest src/tests/test_parser.py
```
