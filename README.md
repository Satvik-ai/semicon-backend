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
7. Local Pinecone via Docker
    1. Install Docker Desktop

        Download and install from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop). Once installed, open Docker Desktop and make sure it's running (you'll see the Docker whale icon in your taskbar/menu bar).

        Verify in terminal:
        ```bash
        docker --version
        # Should print: Docker version 26.x.x ...
        ```
    2. Pull the Pinecone local image
        ```bash
        docker pull ghcr.io/pinecone-io/pinecone-local:latest
        ```
        This downloads the image (~500MB). Only needed once.
    3. Run the container
        ```bash
        docker run -d \
        --name pinecone-local \
        -p 5081:5081 \
        -p 5082:5082 \
        ghcr.io/pinecone-io/pinecone-local:latest
        ```

        What each flag means:
        - `-d` — run in background (detached mode), doesn't block your terminal
        - `--name pinecone-local` — gives the container a friendly name so you can reference it easily
        - `-p 5081:5081` — maps port 5081 on your laptop to port 5081 inside the container (this is the API port your Django app talks to)
        - `-p 5082:5082` — maps port 5082 (this is the web dashboard)
    4. Verify it's running
        ```bash
        docker ps
        ```
        You should see:
        ```
        CONTAINER ID   IMAGE                                      STATUS         PORTS
        abc123def456   ghcr.io/pinecone-io/pinecone-local:...    Up 10 seconds  0.0.0.0:5081->5081/tcp, 0.0.0.0:5082->5082/tcp
        ```

        Then test the API is actually responding:
        ```bash
        curl http://localhost:5081/indexes
        # Should return: {"indexes":[]}
        ```
    5. Open the dashboard (optional)

        Open your browser and go to `http://localhost:5082`. You'll see a web UI where you can browse your indexes and vectors visually — useful for debugging.

        When Django starts, `pinecone_client.py` connects to `http://localhost:5081` and creates the `semicon-index` if it doesn't exist yet. You'll see the index appear in the dashboard at `http://localhost:5082`.

        ---

        ### Day-to-day commands

        ```bash
        # Stop the container (when you're done for the day)
        docker stop pinecone-local

        # Start it again next day (no need to docker run again)
        docker start pinecone-local

        # Check logs if something seems wrong
        docker logs pinecone-local

        # Delete container completely (data is lost — index recreated on next Django start)
        docker rm -f pinecone-local
        ```

        > **Important:** The local Pinecone container stores data **in memory**. When you stop and remove the container, all vectors are lost. When you restart it, your Django app will recreate the empty index, but you'll need to re-upload your PDFs to repopulate it. This is fine for development — in production you'd use Pinecone's cloud which persists data permanently.
8. Run the Django app normally

    ```bash
    python manage.py runserver
    ```



