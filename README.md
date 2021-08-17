# ToDoFehrist
RESTful API for ToDo List application developed in PPDL (Python-PostgreSQL-Django-Linux) stack.

## Run Project
    - Set Environment Variables
        1: ENV = 'DEV' or 'QA' or 'UAT' or 'PROD'
        2: SECRET_KEY = 'Your_Django_SECRET_KEY'
        3: DATABASE = 'sqlite' or 'postgresql'
        For PostgreSQL DB setup only:
            3.1: DB_HOST = 'database_host_name'
            3.2: DB_NAME = 'database_name'
            3.3: DB_USER = 'database_username'
            3.4: DB_PASSWORD = 'database_password'
            3.5: DB_PORT = database_port_number
        If any environment variable isn't set, then an exception will be thrown.