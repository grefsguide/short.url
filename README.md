# short.url

API для сокращения ссылок с аутентификацией, тегами и статистикой переходов.

## 📋 Основные возможности
- Сокращение длинных URL
- Кастомные алиасы для ссылок
- Группировка ссылок по тегам
- Редактирование ссылки и тега
- Статистика переходов
- Автоматическое удаление старых ссылок
- Поиск по ссылке или тегу
- Удаление своих ссылок (чужие нельзя)
- Просмотр ссылок с истекшим сроком(только свои)
- JWT аутентификация

## 🚀 Примеры запросов

### Регистрация
```bash
curl -X 'POST' \
  'http://localhost:8000/auth/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "password": "string"
}'
```
### Вход
```bash
curl -X 'POST' \
  'http://localhost:8000/auth/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "password": "string"
}'
```
### Создание сокращенной ссылки (с кастомным алиас и меткой)
```bash
    curl -X POST "http://localhost:8000/api/links/shorten" \
    -H "Content-Type: application/json" \
    -d '{
      "original_url": "https://example.com/long-url",
      "custom_alias": "my-link",
      "tag_name": "example"
    }'
```

### Поиск ссылок (как по url, так и по метке)
```bash
curl -X GET "http://localhost:8000/api/links/search?search_term=example&tag_name=test"
```
### Получение неактивных ссылок
```bash
curl -X GET "http://localhost:8000/api/links/exp_links" \
  -H "Authorization: Bearer <your_token>"
```
### Изменение ссылок (url и метки)
```bash
curl -X 'PUT' \
  'http://localhost:8000/api/links/{short_code}' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "original_url": "string",
  "tag_name": "string"
}'
```
### Перенаправление на ссылку
```bash
curl -X 'GET' \
  'http://localhost:8000/api/links/{short_code}' \
  -H 'accept: application/json'
```
### Удаление ссылок
```bash
curl -X 'DELETE' \
  'http://localhost:8000/api/links/{short_code}' \
  -H 'accept: application
```
### Получение статистики
```bash
curl -X 'GET' \
  'http://localhost:8000/api/links/{short_code}/stats' \
  -H 'accept: application/json'
```

### Выход
```bash
curl -X 'POST' \
  'http://localhost:8000/auth/logout' \
  -H 'accept: application/json' \
  -d ''
```

## 🛠 Установка и запуск
Требования:
- Docker и Docker Compose
- Python 3.11
1) Клонируете репозиторий
2) Создаёте .env примерно такого вида:
```
DB_USER = 'db_user'
DB_PASS = 'db_pass'
DB_HOST = 'db'
DB_PORT = '5432'
DB_NAME = 'name_db'
ALGORITHM = 'HS256'
REDIS_URL = 'redis://redis:6379'
SECRET_KEY = 'your-secret-key'
```
3) Запускаете Docker и alembic

## 🗄 Структура БД
Таблицы:

- links

| Поле	| Тип	| Описание |
|-------|---------|--------------|
| `id`	| SERIAL	| Первичный ключ| 
|`original_url`	| VARCHAR	| Оригинальный URL |
| `short_code`	| VARCHAR	| Сокращенный код |
| `created_at` | TIMESTAMP	| Дата создания |
| `last_used_at` | TIMESTAMP | Время последнего нажатия |
| `expires_at`	| TIMESTAMP	| Срок действия |
| `is_active`	| BOOLEAN	| Активна ли ссылка |
| `owner_id`	| INTEGER	| Владелец (FK → users) |
|`tag_id`	| INTEGER	| Тег (FK → tags) |

- tags 

| Поле | Тип	| Описание |
|------|-----|-----------|
| `id` | SERIAL	| Первичный ключ |
| `name` |	VARCHAR(50)	| Уникальное имя тега |

- users

| Поле	| Тип	| Описание |
|------|------|---------|
| `id`	| SERIAL	| Первичный ключ |
| `email` |	VARCHAR	| Уникальный email |
| `hashed_pass` |	VARCHAR	| Хэш пароля |

## Тесты

Тысты покрывают 92%, чтобы посмотреть htmlcov/index.html

Для запуска тестов вводим команду:
```bash
$ pytest -W ignore -v --cov=src
```
Нагрузочный тест:
Если меняли хоста и порт, то подставьте свои в {}
```bash
$ locust -f tests/load_test/locustfile.py --host http://{host}:{port}
