# Competitive Wikipedia Speedrunning

This repository holds the code for [wikispeedruns.com](https://wikispeedruns.com).

## 1. Prerequisites

- Docker

## 2. Docker Setup

- Clone and `cd` into the repo
- Run `sudo docker-compose build && sudo docker-compose up`
  - This will build and host the website, however the MySQL database as not been set up yet.
- Enter the docker MySQL with `sudo docker-compose exec mysql mysql -u root -p` and login with password `rootpassword`.
- Copy and run the commands from `./scripts/init.sql` into the MySQL command line. You can also just copy paste them from here:

```sql
CREATE USER 'user'@'%';
GRANT ALL PRIVILEGES ON wikipedia_speedruns.* TO 'user'@'%';
FLUSH PRIVILEGES;
```

- This will set up a user (`user`) with no password that controls the `wikipedia_speedrun` database.
- To set up the rest of the database, you can run the pre-written Python scripts:

```bash
sudo docker-compose exec backend python scripts/create_db.py
sudo docker-compose exec backend python scripts/create_admin_account.py
sudo docker-compose exec backend python scripts/populate_db.py
```

- These scripts will set up the `wikipedia_speedruns` database, create an admin account for you, and populate the database with testing data.

## 3. Testing Locally

- To test your code locally, you will need to set up a new user called `testuser`, which has access to a new database called `test`.
- Then, run `sudo docker-compose exec backend /bin/bash` to enter into the Docker container.
- Run

```bash
cd test
pytest
```

to run the tests.
