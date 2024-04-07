# Buses Plus Web

This is a web application for managing buses.

## Setup

### Create and activate the virtual environment

1. Create a virtual environment using the following command:
    ```sh
    python -m venv env
    ```

   Note: If you encounter a virtualenv error, install the 'virtualenv' package by running:
   ```sh
   pip install virtualenv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```sh
        .\env\Scripts\activate
     ```
   - On Mac/Linux:
     ```sh
         source env/bin/activate
     ```

### Install dependencies

Install the required Python packages by running the following command:
```sh
pip install -r requirements.txt
```

### Setup Database
install postgress database (Linux)
```
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql.service
```
### Create Role  and  database

```
sudo -u postgres psql
CREATE DATABASE buses;
CREATE USER zohaib WITH PASSWORD 'root';
ALTER ROLE zohaib SET client_encoding TO 'utf8';
ALTER ROLE zohaib SET default_transaction_isolation TO 'read committed';
ALTER ROLE zohaib SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE buses TO zohaib;
\q
```
### Prerequireties

* install redis and run
```
sudo apt install lsb-release curl gpg
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

sudo apt-get update
sudo apt-get install redis
redis-server
```
* run  celery in terminal
```
celery -A buses worker
```
* run celery beat 
```
celery -A buses beat -l info -S django
```
### Apply database migrations

Apply the initial database migrations using the following command:
```sh
python manage.py migrate
```

### Run the development server

Start the development server with the following command:
```sh
python manage.py runserver
```

The application will be accessible at http://localhost:8000/.

## Contributing

If you'd like to contribute to this project, please follow these steps:

1. Create a new branch with a descriptive name for your feature or bug fix.
2. Make your changes and commit them with clear commit messages.
3. Push your changes to your forked repository.
4. Submit a pull request to the original repository, explaining your changes.
## License

This project is licensed under the MIT License.