import pymysql
import json

import argparse
import os

DEFAULT_DB_NAME='wikipedia_speedruns'

docker_fp = "/app/config/default.json"

def create_database(db_name, recreate=False, test_config=None):
    # Load database settings from
    # config = json.load(open("../config/default.json"))
    config = json.load(open(docker_fp))
    print(config)
    try:
        # config.update(json.load(open("../config/prod.json")))
        config.update(json.load(open(docker_fp)))
    except FileNotFoundError:
        pass

    if test_config:
        config.update(test_config)

    conn = pymysql.connect(
        user=config["MYSQL_USER"],
        host=config["MYSQL_HOST"],
        password=config["MYSQL_PASSWORD"],
    )


    with conn.cursor() as cursor:
        if (recreate):
            drop_db_query = f'DROP DATABASE IF EXISTS {db_name}'
            cursor.execute(drop_db_query)

        create_db_query = f'CREATE DATABASE IF NOT EXISTS {db_name}'
        cursor.execute(create_db_query)
        use_db_query = f'USE {db_name}'
        cursor.execute(use_db_query)

        with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
            sql = f.read()

            for query in sql.split(';'):
                if len(query.strip()) == 0: continue
                cursor.execute(query)

        conn.commit()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create the db for wikispeedruns.')
    parser.add_argument('--db_name', default=DEFAULT_DB_NAME)
    parser.add_argument('--recreate', action='store_true')

    args = parser.parse_args()
    create_database(args.db_name, recreate=args.recreate)

