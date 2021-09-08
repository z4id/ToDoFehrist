# ToDoFehrist
## _Last ToDo List App, Ever_

[![N|Solid](https://www.python.org/static/img/python-logo.png)](https://www.python.org/)

RESTful API for ToDo List application developed in PPDL (Python-PostgreSQL-Django-Linux) stack.

## Features

- Add upto 50 tasks per user
- Set due datetime for completion
- Track your progress via simplified reports
- Recieve reminders every day for pending tasks via email

## Tech

- [Python] - Python
- [Django] - Django
- [DRF] - Django Rest Framework
- [Celery] - Celery

EnvConfigurator is open source with a [public repository][todofehrist] on GitHub.

## Set Environment Variables
    1: SECRET_KEY = 'Your_Django_SECRET_KEY'
        2.1: DB_HOST = 'database_host_name'
        2.2: DB_NAME = 'database_name'
        2.3: DB_USER = 'database_username'
        2.4: DB_PASSWORD = 'database_password'
        2.5: DB_PORT = database_port_number
    3: LOG_LEVEL = 'INFO' or 'DEBUG' or 'WARNING' or 'ERROR' (Optional, default: 'INFO')
    6: LOG_FILE = 'PATH_TO_LOG_FILE' (Optional, default: 'todofehrist_api.log')
    7: ALLOWED_HOST: 'Ip_Address_1,Ip_Address_2' # comma separated
    8: GOOGLE_OAUTH_CLIENT_ID: 'Google unique Apps Client ID'
    
    If any environment variable isn't set, then an exception will be thrown.

## Installation & Usage

ToDoFehrist requires [Python3.8](https://pypi.org/), Django3, DRF3 & Celery5 to run.

```sh
source dev.env
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata fixture_2
python manage.py test
python manage.py runserver
```

## Celery
```sh
apt install redis
celery -A emumbaproject.celery worker --loglevel=info
celery -A emumbaproject.celery beat -l debug
```

## Docker Compose
```sh
docker-compose build
docker-compose up -d

# Build the new image and spin up the two containers: 
docker-compose up -d --build

# Goto to your ALLOWED_HOST_Value:8000/doc/
docker-compose exec db psql --username=$DB_USER --dbname=$DB_NAME
docker volume inspect todofehrist_postgres_data
```

## Development

Want to contribute? Great!

Fork Github repository and create a Pull Request.

Run tests before submitting the request
```sh
python manage.py test
pylint --load-plugins pylint_django $(git ls-files '*.py')
```

## License

MIT

**Free Software, Hell Yeah!**

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [todofehrist]: <https://github.com/z4id/ToDoFehrist>
   [@z_4id]: <http://twitter.com/z_4id>
