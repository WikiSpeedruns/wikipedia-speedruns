from app import app

from flask import render_template, request, redirect, session

from util.decorators import check_admin

import db

# Passes session args to function if needed
def render_with_user(template, **kwargs):
    if ("user_id" in session):
        return render_template(template, user_id=session["user_id"], username=session["username"], **kwargs)
    else:
        return render_template(template, **kwargs)

# Front end pages
@app.route('/', methods=['GET'])
def get_home_page():    
    return render_with_user('home.html')

@app.route('/random', methods=['GET'])
def get_random_prompt():
    # TODO this is insanely inefficient, it needs to sort the whole set of public prompts!
    query = ("""
    SELECT prompt_id FROM prompts
    WHERE public=TRUE
    ORDER BY RAND()
    LIMIT 1;
    """)

    with db.get_db().cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchone()
        print(results)
        return redirect("/play/" + str(results[0]), code=302)

@app.route('/latest', methods=['GET'])
def get_latest_prompt():
    # TODO its a little messy to do this here
    query = ("SELECT MAX(prompt_id) FROM prompts WHERE public=TRUE;")

    with db.get_db().cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchone()
        return redirect("/play/" + str(results[0]), code=302)

@app.route('/register', methods=['GET'])
def get_register_page():
    return render_with_user('users/register.html')

@app.route('/pending', methods=['GET'])
def get_create_oauth_account_page():
    if ("pending_oauth_creation" in session):
        return render_with_user('users/pending.html')
    else:
        return redirect('/')

@app.route('/login', methods=['GET'])
def get_login_page():
    return render_with_user('users/login.html')

@app.route('/profile/<username>', methods = ['GET'])
def get_profile_page(username):
    return render_with_user('profile.html', un=username)

@app.route('/manage', methods=['GET'])
@check_admin
def get_manage_page():
    return render_with_user('manage.html')

@app.route('/prompt/<id>', methods=['GET'])
def get_prompt_page(id):
    run_id = request.args.get('run_id', '')
    
    if len(run_id) != 0:
        return render_with_user('prompt.html', prompt_id=id, run_id=run_id)
    else:
        return render_with_user('prompt.html', prompt_id=id)


@app.route('/play/<id>', methods=['GET'])
def get_play_page(id):
    return render_with_user('play.html', prompt_id=id)



@app.route('/marathon/<id>', methods=['GET'])
def get_marathon_play_page(id):
    print(id, "Loading")
    return render_with_user('marathon.html', prompt_id=id)

#@app.route('/prompt/marathon/<id>', methods=['GET'])
#def get_marathon_prompt_page(id):
#    run_id = request.args.get('run_id', '')
#    
#    if len(run_id) != 0:
#        return render_with_user('marathon_prompt.html', prompt_id=id, run_id=run_id)
#    else:
#        return render_with_user('marathon_prompt.html', prompt_id=id)
    


@app.route('/confirm/<token>', methods=['GET'])
def get_confirm_page(token):
    return render_with_user('users/confirm_email.html', token=token)

@app.route('/reset/request', methods=['GET'])
def get_reset_request_page():
    return render_template('users/reset_password_request.html')

@app.route('/reset/<id>/<token>', methods=['GET'])
def get_reset_page(id, token):
    return render_template('users/reset_password.html', id=id, token=token)
