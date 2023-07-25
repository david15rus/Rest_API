# FastAPI_project

Данный API предлагается в дух видах: синхронном и асинхронном.
API позволяет совершать CRUD операции посредством использования ORM SQLAlchemy 
и СУБД PostgresSQL

## Требования
Для правильного функционирования API необходимо, что бы 
все версии библиотек и модулей соотвествовали файлу requirements.txt.
А также версии Python и Postgres:
- Python 3.10 (или новее)
- PostgreSQL 15 (или новее)

## Установка
1. Создайте виртуальное окружение и активируйте его:
python -m venv venv
source venv/bin/activate  # Для Windows используйте `venv\Scripts\activate`
3. Склонируйте репозиторий:
git clone https://github.com/david15rus/Rest_API.git
4. Установите зависимости:
pip install -r requirements.txt
5. Создайте базу данных:
Алгоритм создание БД через админку можно посмотреть по ссылке https://metanit.com/sql/postgresql/2.1.php
6. В файл config.py измените константу в соотвествии с вашей базой данных где
DATABASE_URL = "postgresql://<username>:<password>@localhost/<название_бд>" - для синхронной API
DATABASE_URL_ASYNCIO = "postgresql+asyncpg://<username>:<password>@localhost/<название_бд>" - для асинхронной API

## Запуск
1. Для запуска синхронной версии выполните команду uvicorn main:app --reload
2. Для запуска асинхронной версии выполните команду uvicorn main_asyncio:app --reload
