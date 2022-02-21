'''
Script that generates configuration for server, as well as adds admin account
'''

import json
import secrets

from getpass import getpass

import pymysql

from wikispeedruns.auth import passwords

def create_prod_conf():
    config = {}
    config["SECRET_KEY"] = str(secrets.token_urlsafe(20))
    config["GOOGLE_OAUTH_CLIENT_ID"] = input("Google Client ID for Oauth: ")
    config["GOOGLE_OAUTH_CLIENT_SECRET"] = input("Google Secret for Oath: ")
    # TODO more here

    config["MAIL_SERVER"] = input("Mail Server URL: ")
    config["MAIL_PORT"] = input("Mail Server Port: ")
    config["MAIL_USERNAME"] = input("SMTP Username: ")
    config["MAIL_PASSWORD"] = input("SMTP Password: ")
    config["MAIL_DEFAULT_SENDER"] = input("Default Sender for mail: ")


    json.dump(config, open('../config/prod.json', 'w'), indent=4)

def create_admin_account():
    config = json.load(open('../config/default.json'))

    # load prod settings if they exist
    try:
        config.update(json.load(open('../config/prod.json')))
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

    hash = passwords.hash_password(password)


    query = "INSERT INTO `users` (`username`, `hash`, `email`, `email_confirmed`, `admin`) VALUES (%s, %s, %s, %s, %s)"

    db = pymysql.connect(
            user=config["MYSQL_USER"], 
            host=config["MYSQL_HOST"],
            password=config["MYSQL_PASSWORD"], 
            database=config['DATABASE']
    )

    with db.cursor() as cursor:
        result = cursor.execute(query, (username, hash, email, True, True))

        if (result == 0):
            print("User {} already exists".format(username))
        else:
            print("Admin User {} added".format(username))
        db.commit()
    db.close()


ans = input("Would you like to setup configuration for production? (y/n): ")
if (ans == "y"):
    create_prod_conf()

ans = input("Would you like to setup an admin account? (y/n): ")

while (ans == "y"):
    create_admin_account()
    ans = input("Would you like to setup another admin account? (y/n): ")