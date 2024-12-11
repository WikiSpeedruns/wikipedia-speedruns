'''
Create some example users/prompts/runs etc. for local dev
'''
import datetime
import secrets
import pymysql
import json

import bcrypt
import hashlib
import base64

import argparse
import os

DEFAULT_DB_NAME='wikipedia_speedruns'
docker_fp = "/app/config/default.json"

def populate_sprints(cursor):
    # Create a bunch of daily prompts of the form '[n] (number)' -> '[n + 1] (number)'
    # 20 - 50 are dailys starting from 15 days ago
    # 50 - 60 are unused
    prompts = []

    now = datetime.datetime.now()

    for i in range(40):
        prompt_start = f"{20 + i} (number)"
        prompt_end = f"{20 + i + 1} (number)"
        day = (now - datetime.timedelta(days=(15 - i))).date()
        prompts.append((prompt_start, prompt_end, day, day + datetime.timedelta(days=1)))

    query = '''
        INSERT INTO `sprint_prompts` (`start`, `end`, `rated`, `active_start`, `active_end`)
        VALUES (%s, %s, 1, %s, %s)
    '''
    cursor.executemany(query, prompts[:30])

    # unused prompts
    query = '''
        INSERT INTO `sprint_prompts` (`start`, `end`)
        VALUES (%s, %s)
    '''
    cursor.executemany(query, [(start, end) for (start, end, _, _) in prompts[30:]])


def populate_marathon_prompts(cursor):
    # Create a bunch of marathon prompts
    prompts = []
    checkpoints = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    for i in range(40):
        checkpoints.append(f"{20 + i} (number)")

    for i in range(10):
        reordered = checkpoints[2*i:] + checkpoints[:2*i]
        start = reordered[0]
        startcps = reordered[1:6]
        cps = reordered[6:]
        seed = i
        prompts.append((start, json.dumps(startcps), seed, json.dumps(cps)))

    query = "INSERT INTO `marathonprompts` (start, initcheckpoints, seed, checkpoints) VALUES (%s, %s, %s, %s);"
    cursor.executemany(query, prompts)


def populate_users(cursor):
    # Create 40 users with username/password of testuser[i]/testuser[i] for i 1-40
    query = "INSERT INTO `users` (`username`, `hash`, `email`, `join_date`) VALUES (%s, %s, %s, %s)"

    users = []
    date = datetime.datetime.now() - datetime.timedelta(days=40)
    for i in range(40):
        username = f"testuser{i+1}"
        hash = bcrypt.hashpw(base64.b64encode(hashlib.sha256(username.encode()).digest()), bcrypt.gensalt())
        email = username + "@testemail.com"
        date = date + datetime.timedelta(days=1)
        users.append((username, hash, email, date))

    try:
        cursor.executemany(query, users)
    except pymysql.IntegrityError as e:
        print("testuser(s) already exist, continuing...")


def populate_runs(cursor):
    # Create a run for each user on all currently archived prompts
    users_query = "SELECT user_id FROM users"
    prompts_query = """
        SELECT prompt_id, start, end, active_start, active_end FROM sprint_prompts
        WHERE used=1 AND active_start <= NOW()
    """
    runs_query = """
        INSERT INTO sprint_runs (prompt_id, user_id, start_time, end_time, play_time, finished, path)
        VALUES (%(prompt_id)s, %(user_id)s, %(start_time)s, %(end_time)s, %(play_time)s, %(finished)s, %(path)s)
    """

    cursor.execute(users_query)
    users = cursor.fetchall()

    cursor.execute(prompts_query)
    prompts = cursor.fetchall()

    runs = []
    for p in prompts:
        if (p['active_start'] is None): continue

        run_time = 50

        for u in users:
            start_time = p["active_start"] + datetime.timedelta(hours=4)
            end_time = p["active_start"] + datetime.timedelta(hours=4, seconds=run_time)
            path = json.dumps({
                "version": "2.1",
                "path": [
                    {
                        "article": p["start"],
                        "loadTime": 0,
                        "timeReached": 0
                    },
                    {
                        "article": p["end"],
                        "loadTime": 0,
                        "timeReached": 0
                    }
                ]
            })

            runs.append({
                "prompt_id": p["prompt_id"],
                "user_id": u["user_id"],
                "start_time": start_time,
                "end_time": end_time,
                "play_time": (end_time - start_time).total_seconds(),
                "finished": True,
                "path": path,
            })
            run_time += 20


    cursor.executemany(runs_query, runs)


def populate_marathon_runs(cursor):
    # Create a run for each user on all marathon prompts
    users_query = "SELECT user_id FROM users"
    prompts_query = """
        SELECT prompt_id, start, initcheckpoints, checkpoints FROM marathonprompts
    """
    runs_query = "INSERT INTO `marathonruns` (`path`, `prompt_id`, `user_id`, `checkpoints`, `total_time`, `finished`) VALUES (%s, %s, %s, %s, %s, %s)"

    cursor.execute(users_query)
    users = cursor.fetchall()

    cursor.execute(prompts_query)
    prompts = cursor.fetchall()

    runs = []
    count = 0

    for p in prompts:

        run_time = 10000
        startcp = json.loads(p['initcheckpoints'])
        cp = json.loads(p['checkpoints'])

        for u in users:

            path1 = json.dumps([p["start"], startcp[0], startcp[1], cp[0]])
            checkpoints1 = json.dumps([startcp[0], startcp[1], cp[0]])

            path2 = json.dumps([p["start"], startcp[0], startcp[1]] + cp[:5])
            checkpoints2 = json.dumps([startcp[0], startcp[1]] + cp[:5])

            runs.append((
                path1,
                p["prompt_id"],
                u["user_id"],
                checkpoints1,
                run_time,
                count%2
            ))

            count += 1
            run_time += 200
            runs.append((
                path2,
                p["prompt_id"],
                u["user_id"],
                checkpoints2,
                run_time,
                count%2
            ))
            count += 1

    cursor.executemany(runs_query, runs)


def populate_lobbies(cursor):
    # Create a lobby for each user
    users_query = "SELECT user_id, join_date FROM users"

    lobby_query = """
        INSERT INTO `lobbys` (`name`, `desc`, passcode, create_date, active_date, rules)
        VALUES (%(name)s, %(desc)s, %(passcode)s, %(date)s, %(date)s, %(rules)s);
    """
    
    user_lobbys_query = """
        INSERT INTO `user_lobbys` (user_id, lobby_id, `owner`)
        VALUES (%s, %s, 1);
    """

    cursor.execute(users_query)
    users = cursor.fetchall()

    for i, user in enumerate(users):
        user_id = user["user_id"]
        date = user["join_date"]
        passcode = "".join([str(secrets.randbelow(10)) for _ in range(6)])  # XXX: this is from thing

        cursor.execute(lobby_query, {
            "name": f"lobby{i+1}",
            "desc": f"test lobby {i+1}",
            "passcode": passcode,
            "date" : date,
            "rules": json.dumps({})
        })

        lobby_id = cursor.lastrowid
        cursor.execute(user_lobbys_query, (user_id, lobby_id))


def populate_lobby_prompts(cursor):
    # Add lobby prompts of the form '[n] (number)' -> '[n + 1] (number)'
    # to each existing lobby
    lobby_query = """
        SELECT l.lobby_id, IFNULL(MAX(prompt_id), 0) AS max_prompt_id
        FROM
            lobbys AS l
                LEFT JOIN 
            lobby_prompts AS p ON l.lobby_id = p.lobby_id
        GROUP BY l.lobby_id
    """
    cursor.execute(lobby_query)
    lobbies = cursor.fetchall()

    prompts = []    
    for lobby in lobbies:
        lobby_id = lobby["lobby_id"]
        prompt_id = lobby["max_prompt_id"]

        for i in range(10):
            prompt_start = f"{20 + i} (number)"
            prompt_end = f"{20 + i + 1} (number)"

            prompts.append({
                "lobby_id": lobby_id,
                "prompt_id": prompt_id + i + 1,
                "start": prompt_start,
                "end": prompt_end,
                "language": "en",
            })

    prompt_query = """
        INSERT INTO `lobby_prompts` (`lobby_id`, `prompt_id`, `start`, `end`, `language`)
        VALUES (%(lobby_id)s, %(prompt_id)s, %(start)s, %(end)s, %(language)s);
    """
    cursor.executemany(prompt_query, prompts)


def populate_lobby_runs(cursor):
    # Create a run for each user on all currently archived prompts
    users_query = "SELECT user_id FROM users"
    lobby_prompts_query = """
        SELECT lobby_id, prompt_id, start, end FROM lobby_prompts
    """
    runs_query = """
        INSERT INTO lobby_runs (lobby_id, prompt_id, user_id, name, start_time, end_time, play_time, finished, path)
        VALUES (%(lobby_id)s, %(prompt_id)s, %(user_id)s, %(name)s, %(start_time)s, %(end_time)s, %(play_time)s, %(finished)s, %(path)s)
    """

    cursor.execute(users_query)
    users = cursor.fetchall()

    cursor.execute(lobby_prompts_query)
    lobby_prompts = cursor.fetchall()

    runs = []
    for lobby_prompt in lobby_prompts:

        run_time = 50

        for i, u in enumerate(users):
            start_time = datetime.datetime.now() - datetime.timedelta(len(users) - i)
            end_time = datetime.datetime.now() - datetime.timedelta(len(users) - i)
            path = json.dumps({
                "version": "2.1",
                "path": [
                    {
                        "article": lobby_prompt["start"],
                        "loadTime": 0,
                        "timeReached": 0
                    },
                    {
                        "article": lobby_prompt["end"],
                        "loadTime": 0,
                        "timeReached": 0
                    }
                ]
            })

            runs.append({
                "lobby_id": lobby_prompt["lobby_id"],
                "prompt_id": lobby_prompt["prompt_id"],
                "user_id": u["user_id"],
                "name": None,
                "start_time": start_time,
                "end_time": end_time,
                "play_time": (end_time - start_time).total_seconds(),
                "finished": True,
                "path": path,
            })
            run_time += 20

    cursor.executemany(runs_query, runs)


def populate_quick_runs(cursor):
    # Add quick runs. Each user has 10 runs, 8 of which are completed. 

    users_query = "SELECT user_id, join_date FROM users"
    cursor.execute(users_query)
    users = cursor.fetchall()

    num_per_user = 10
    runs = []

    for u, user in enumerate(users):
        user_id = user["user_id"]
        join_date = user["join_date"]
        for i in range(num_per_user):
            start_article = f"{u*num_per_user + i} (number)"
            end_article = f"{u*num_per_user + i + 1} (number)"
            start_time = join_date + datetime.timedelta(minutes=i)
            end_time = start_time + datetime.timedelta(minutes=10)
            play_time = (end_time - start_time).total_seconds()
            path = json.dumps({
                "version": "2.1",
                "path": [
                    {
                        "article": start_article,
                        "loadTime": 0,
                        "timeReached": 0
                    },
                    {
                        "article": end_article,
                        "loadTime": 0,
                        "timeReached": 0
                    }
                ]
            })
            
            runs.append({
                "user_id": user_id,
                "prompt_start": start_article,
                "prompt_end": end_article,
                "finished": i < 8,
                "language": 'en',
                "start_time": start_time,
                "end_time": end_time,
                "path": path,
                'play_time': play_time,
            })

    prompt_query = """
        INSERT INTO `quick_runs` (`user_id`, `prompt_start`, `prompt_end`, `finished`, `language`, `start_time`, `end_time`, `path`, `play_time`)
        VALUES (%(user_id)s, %(prompt_start)s, %(prompt_end)s, %(finished)s, %(language)s, %(start_time)s, %(end_time)s, %(path)s, %(play_time)s);
    """
    cursor.executemany(prompt_query, runs)


def populate_database(db_name, recreate=False):
    # Load database settings from
    config = json.load(open(docker_fp))
    try:
        config.update(json.load(open(docker_fp)))
    except FileNotFoundError:
        pass

    conn = pymysql.connect(
        user=config["MYSQL_USER"],
        host="mysql",  # Use the MySQL service name here
        password=config["MYSQL_PASSWORD"],
        database=db_name
    )


    with conn.cursor(cursor=pymysql.cursors.DictCursor) as cursor:
        populate_quick_runs(cursor)
        populate_sprints(cursor)
        populate_users(cursor)
        populate_runs(cursor)
        populate_marathon_prompts(cursor)
        populate_marathon_runs(cursor)
        populate_lobbies(cursor)
        populate_lobby_prompts(cursor)
        populate_lobby_runs(cursor)
        

        conn.commit()
        conn.close()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create the db for wikispeedruns.')
    parser.add_argument('--db_name', default=DEFAULT_DB_NAME)

    args = parser.parse_args()
    populate_database(args.db_name)

