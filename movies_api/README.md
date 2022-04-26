# movies_api - Сервис Async API (Yandex-Practicum) 

3я команда 14 когорта:
- Сергей Волков
- Илья Мудрицкий
- Александр Камянский

### 1. Клонирование репозиториев
1. Репозитоий где мы будем работать над AsyncAPI
```commandline
git clone git@github.com:kamyanskiy/movies_api.git
```
2. Репозиторий где мы сможем доработать ETL.
```commandline
git clone git@github.com:kamyanskiy/postgres_to_es.git
```


### 2. Проверка версии Python
   Проверьте есть ли у вас в системе Python 3.10.x, если нет можно с помощью 
   pyenv https://github.com/pyenv/pyenv инструмента установить необходимую 
   версию Python (у меня на данный момент 3.10.4).


### 3. Установка зависимостей 
   Установка зависимостей подразумевает, что вы пользуетесь poetry для 
   управления зависимостями, если нет, то туториал по установке 
   тут https://python-poetry.org/docs/. Если возникнут сложности, 
   обращайтесь ко мне и все поправим.
   Собственно сама установка:
```commandline
cd movies_api
poetry install
```
### 4. Redis + Elasticsearch + sqlite_to_postgres + postgres_to_es(ETL)
   В данный момент наша начальная версия проекта нуждается в запущенном 
   инстансе redis и elasticsearch в котором есть данные из предыдущего 
   задания про ETL. Так как в код нашего микросервиса нельзя встаривать код 
   по сути отдельного микросервиса ETL, предлагаю запускать стек пока вот 
   так, я добавляю в наш docker-compose.yml следущее: 
   1. elasticsearch.
   2. kibana (чтоб адекватно посмотреть что в эластике).
   3. postgres db.
   4. sqlite_to_postgres (сервис который наполнит пустой postgres данными из 
      sqlite db).
   5. postgres_to_es (репо которое лежит рядом с movies_api) там будет код 
      ETL который будет билдиться и запускаться в общем docker-compose. При 
      запуске он наполнит эластик данными из postgres. Посмотрите на мой 
      docker-compose.yml, если есть вопросы, обсудим.
   6. movies_admin (она нам нужна только чтоб запустились миграции, если 
      постгрес пустой, ну и по совету наставника она типа часть нашего стека).
   7. nginx (web server, с reverse прокси для админки).
   8. movies_api - наш сервис async API который разрабатываем.
   
   Есть файлы конфигов .env.*.sample которые нужно переименовать в без .
   sample и поправить креденшлы подключения к бд.    

   Запускаем сервисы (если не хотим чтоб movies_api запустился в контейнере 
не указываем его в перечислении, иначе делаем просто `docker-compose up 
  --build`):
   ```commandline
   (находясь в каталоге movies_api)
   docker-compose up --build --no-deps nginx movies_admin db es01 kibana redis sqlite_to_pg postgres_to_es
   ```
   
### 5. Запуск movies_api проекта локально (который разрабатываем)
```commandline
poetry shell
python src/main.py
```
Должно получиться что то вот примерно так:
```commandline
(movies-api-_GigOhHC-py3.10) ➜  movies_api git:(master) ✗ python src/main.py
2022-04-12 21:22:36,806 - uvicorn.error - INFO - Started server process [198101]
2022-04-12 21:22:36,806 - uvicorn.error - INFO - Waiting for application startup.
2022-04-12 21:22:36,807 - uvicorn.error - INFO - Application startup complete.
2022-04-12 21:22:36,808 - uvicorn.error - INFO - Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

```
Проверим что наше приложение может достучаться до редиса и эластика
```commandline
curl --location --request GET 'http://0.0.0.0:8000/api/v1/films/479f20b0-58d1-4f16-8944-9b82f5b1f22a'
```
в ответ должен прийти ответ
```commandline
{"id":"479f20b0-58d1-4f16-8944-9b82f5b1f22a","title":"The Soap-Suds Star"}
```

Также можно проверить если вы запустили:
```commandline
docker-compose up --build
```
Подождать чтоб все запустилось и можно также проверить что приложение 
отвечает как показано curl запросом выше.

### 6. Flake8, pre-commit
Добавлены также pre-commit-config.yaml для автоматич проверки соотв pep8 при 
коммите, чтоб активировать пре-коммит для этого у себя в папке movies_api 
после установки зависимостей нужно сделать.
```commandline
pre-commit install
```
тогда когда вы будете делать git commit у вас будет отрабатывать прекоммит 
хук и проверять *.py файлы в src каталоге.

### 7. Github-actions
Также можете посмотреть добавлены github-actions, опять же прогоняется 
flake8 после каждого пуша в репо (.github/workflows/code-checker.yaml).

