# ToDoFehrist
RESTful API for ToDo List application developed in PPDL (Python-PostgreSQL-Django-Linux) stack.

API Documentation: http://server_ip/doc/

## Run Project
    - Set Environment Variables
        source env_vars.rc

        1: ENV = 'DEV' or 'QA' or 'UAT' or 'PROD'
        2: SECRET_KEY = 'Your_Django_SECRET_KEY'
        3: DATABASE = 'sqlite' or 'postgresql'
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
    - Run Application
        python manage.py makemigrations
        python manage.py migrate
        python manage.py runserver