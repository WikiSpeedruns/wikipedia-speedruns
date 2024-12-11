import json
import pymysql

import base64
import hashlib
import datetime

from getpass import getpass

import bcrypt


docker_fp = "/app/config/default.json"

def create_admin_account():
    config = json.load(open(docker_fp))

    # load prod settings if they exist
    try:
        config.update(json.load(open(docker_fp)))
    except FileNotFoundError:
        pass

    # Get admin username and password
    username = input("Admin account username (leave blank for 'admin'): " )
    if not username:
        username = 'admin'
    username = username

    email = input("Admin account email (currently not used): ")

    while(True):
        password = getpass("Admin account password: ")
        if password == getpass("Reenter password: "): break
        print("Passwords do not match!")

    hash = bcrypt.hashpw(base64.b64encode(hashlib.sha256(password.encode()).digest()), bcrypt.gensalt())



    query = "INSERT INTO `users` (`username`, `hash`, `email`, `email_confirmed`, `admin`, `join_date`) VALUES (%s, %s, %s, %s, %s, %s)"

    db = pymysql.connect(
    user=config["MYSQL_USER"],
    host=config["MYSQL_HOST"],
    password=config["MYSQL_PASSWORD"],
    database=config['DATABASE']
    )

    with db.cursor() as cursor:
        result = cursor.execute(query, (username, hash, email, True, True, datetime.datetime.now()))

        if (result == 0):
            print("User {} already exists".format(username))
        else:
            print("Admin User {} added".format(username))
        db.commit()
    db.close()


ans = "y"
while (ans == "y"):
    create_admin_account()
    ans = input("Would you like to setup another admin account? (y/n): ")
