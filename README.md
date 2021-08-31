# ToDoFehrist
RESTful API for ToDo List application developed in PPDL (Python-PostgreSQL-Django-Linux) stack.

API Documentation: http://server_ip/doc/

## Run Project
    - Set Environment Variables
        source env_vars.rc

        1: ENV = 'DEV' or 'QA' or 'UAT' or 'PROD'
        2: SECRET_KEY = 'Your_Django_SECRET_KEY'
        3: DATABASE = 'SQLITE' or 'POSTGRESQL'
        For PostgreSQL DB setup only:
            3.1: DB_HOST = 'database_host_name'
            3.2: DB_NAME = 'database_name'
            3.3: DB_USER = 'database_username'
            3.4: DB_PASSWORD = 'database_password'
            3.5: DB_PORT = database_port_number
        4: LOG_LEVEL = 'INFO' or 'DEBUG' or 'WARNING' or 'ERROR' (Optional, default: 'INFO')
        5: LOG_FILE = 'PATH_TO_LOG_FILE' (Optional, default: 'todofehrist_api.log')
        
        If any environment variable isn't set, then an exception will be thrown.
    - Run Tests
        python manage.py test
    - RUN Pylint
        pylint $(git ls-files '*.py')
            Your code has been rated at 6.74/10 
        pylint --load-plugins pylint_django $(git ls-files '*.py')c
            Your code has been rated at 9.43/10 
    - Run Application
        python manage.py makemigrations
        python manage.py migrate
        python manage.py test
        python manage.py loaddata fixture_1
        python manage.py runserver

    - RUn Celery Worker and Celery Beat for scheduling tasks via crontab
        sudo apt install redis
        celery -A emumbaproject.celery worker --loglevel=info
        celery -A emumbaproject.celery beat -l debug