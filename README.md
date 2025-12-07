# Система внутриигровых опросов

Система внутриигровых опросов — это веб‑приложение, позволяющее создавать, проводить и анализировать опросы, встроенные в игровую среду.  
Проект разработан на **Flask**, **PostgreSQL**, **SQLAlchemy**, протестирован с помощью **pytest** и упакован в **Docker**.

---

## Возможности
- Создание опросов через административную панель  
- Добавление вопросов (текстовых, числовых, с вариантами ответа)  
- Публичное прохождение опросов игроками  
- Защита от повторного прохождения по IP  
- REST API для получения списка активных опросов и отправки ответов  
- Хранение данных в PostgreSQL  
- Полное покрытие backend‑части модульными тестами  

---

## Стек технологий
- **Backend:** Python 3.12, Flask, SQLAlchemy  
- **База данных:** PostgreSQL  
- **Контейнеризация:** Docker, Docker Compose  
- **Тестирование:** Pytest 
- **Шаблонизатор:** Jinja2  

---

## Установка и запуск

### 1. Клонировать репозиторий  
```bash
git clone https://github.com/your-repo/survey_app.git
cd survey_app
```

### 2. Запуск системы  
```bash
docker compose up --build
```

После запуска приложение доступно по адресу:  
**http://localhost:8000**

---

## Запуск тестов  
```bash
docker compose run --rm tests
```

---

## API

### Получить список активных опросов
`GET /api/surveys`  
Заголовок обязателен:  
```
X-API-TOKEN: super-secret-api-token
```

### Отправить ответы
`POST /api/surveys/<id>/responses`  
```json
{
  "answers": {
    "1": "Да",
    "2": "18"
  }
}
```

---

## Структура проекта
```
survey_app/
 ├─ app/               
 ├─ templates/
 ├─ static/
 ├─ survey_app/
 │   ├─ models.py
 │   ├─ extensions.py
 │   ├─ wsgi.py
 ├─ tests/            
 ├─ docker-compose.yml
 ├─ Dockerfile
```
