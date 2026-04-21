1. Create virtual environment: 
    - `py -3.11 -m venv venv`
2. Activate the virtual environment: 
    - `.venv\Scripts\activate`
3. Install the required libraries: 
    - `pip install -r requirements.txt`
4. Create Django Project:
    - `django-admin startproject semicon_chatbot_backend .`
    - `python manage.py startapp chat`
    - `python manage.py startapp document`
5. Create PostgreSQL DB
    1. Open pgAdmin > Connect to server > Right-click on Databases > Create Database > Name: `semicon_sb` > Click save
    2. Right-click on Login/Group Roles > Create > Login/Role > Name: `semicon_user` > Password: `semiconpassword` > Under "Privileges" > Set "Can Login" and "Create DB" to Yes > Click save
    3. Databases > semicon_db > Properties > Edit object > Privileges > click on the + (plus) icon to add a new role > In the new row: Select `semicon_user` > Privileges ALL > Click save
    4. Grant privilages to 'semicon_user'. Execute these commands in the SQL terminel of pgadmin:
        `GRANT ALL PRIVILEGES ON DATABASE semicon_db to semicon_user;`
        `\c semicon_db`
        `GRANT ALL ON SCHEMA public to semicon_user;`
        `GRANT USAGE, CREATE ON SCHEMA public to semicon_user;`
        `SET ROLE postgres;`
        `ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO semicon_user;`
        `ALTER DEFAULT PRIVILEGES IN SCHEMA Public GRANT ALL ON SEQUENCES TO semicon_user;`
        `RESET ROLE;`
        `\q`
6. Apply Migrations and Create superuser
    - `python manage.py makemigrations`
    - `python manage.py migrate`
    - `python manage.py createsuperuser`
7. Run the Django app normally
    - `python manage.py runserver`

