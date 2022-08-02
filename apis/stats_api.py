import gzip
import json

from flask import Blueprint, jsonify, make_response
from pymysql.cursors import DictCursor

from util.decorators import check_admin
from util.flaskjson import CustomJSONEncoder
from db import get_db

stats_api = Blueprint("stats", __name__, url_prefix="/api/stats")

@check_admin
@stats_api.get("/totals")
def get_total_stats():
    queries = {}
    queries['total_users'] = "SELECT COUNT(*) AS users_total FROM users"
    queries['total_google_users'] = 'SELECT COUNT(*) AS goog_total FROM users WHERE hash=""'

    queries['total_runs'] = "SELECT COUNT(*) AS sprints_total FROM sprint_runs"
    queries['total_finished_runs'] = "SELECT COUNT(*) AS sprints_finished FROM sprint_runs WHERE finished"
    queries['total_user_runs'] = "SELECT COUNT(*) AS user_runs FROM sprint_runs WHERE user_id IS NOT NULL"
    queries['total_finished_user_runs'] = "SELECT COUNT(*) AS user_finished_runs FROM sprint_runs WHERE user_id IS NOT NULL AND finished"

    queries['total_quick_runs'] = "SELECT COUNT(*) AS quick_runs_total FROM quick_runs"
    queries['total_finished_quick_runs'] = "SELECT COUNT(*) AS quick_runs_finished FROM quick_runs WHERE finished"
    queries['total_user_quick_runs'] = "SELECT COUNT(*) AS user_quick_runs FROM quick_runs WHERE user_id IS NOT NULL"
    queries['total_finished_user_quick_runs'] = "SELECT COUNT(*) AS user_finished_quick_runs FROM quick_runs WHERE user_id IS NOT NULL AND finished"

    queries['total_marathons'] = "SELECT COUNT(*) AS marathons_total FROM marathonruns"
    queries['total_finished_marathons'] = "SELECT COUNT(*) AS marathons_finished FROM marathonruns where finished=TRUE"
    queries['total_user_marathons'] = "SELECT COUNT(*) AS user_marathons FROM marathonruns WHERE user_id IS NOT NULL"
    queries['total_finished_user_marathons'] = "SELECT COUNT(*) AS user_finished_marathons FROM marathonruns WHERE user_id IS NOT NULL AND finished=TRUE"
    
    queries['total_created_lobbies'] = "SELECT COUNT(*) AS lobbies_created FROM lobbys"
    queries['total_lobby_runs'] = "SELECT COUNT(*) AS lobby_runs FROM lobby_runs"
    queries['total_finished_lobby_runs'] = "SELECT COUNT(*) AS lobby_finished_runs FROM lobby_runs WHERE user_id IS NOT NULL"
    results = {}

    db = get_db()
    with db.cursor(cursor=DictCursor) as cursor:
        for _, query in queries.items():
            cursor.execute(query)
            results.update(cursor.fetchall()[0])
        return jsonify(results)


@check_admin
@stats_api.get("/daily")
def get_daily_stats():
    queries = {}
    queries['daily_new_users'] = '''
    WITH data AS (
        SELECT 
            DATE(join_date) AS day,
            COUNT(*) AS daily_users 
        FROM users  
        GROUP BY day 
    )

    SELECT
        day,
        daily_users,
        SUM(daily_users) OVER (ORDER BY day) AS total 
    FROM data
    '''

    queries['daily_sprints'] = '''
    WITH data AS (
        SELECT 
            DATE(start_time) AS day,
            COUNT(*) AS daily_plays 
        FROM sprint_runs
        WHERE start_time IS NOT NULL
        GROUP BY day 
    )

    SELECT
        day,
        daily_plays,
        SUM(daily_plays) OVER (ORDER BY day) AS total 
    FROM data
    '''

    queries['daily_finished_sprints'] = '''
    WITH data AS (
        SELECT 
            DATE(start_time) AS day,
            COUNT(*) AS daily_plays 
        FROM sprint_runs
        WHERE finished
        GROUP BY day 
    )

    SELECT
        day,
        daily_plays,
        SUM(daily_plays) OVER (ORDER BY day) AS total 
    FROM data
    '''
    
    queries['daily_lobby_runs'] = '''
    WITH data AS (
        SELECT 
            DATE(start_time) AS day,
            COUNT(*) AS daily_plays 
        FROM lobby_runs
        WHERE start_time IS NOT NULL
        GROUP BY day 
    )

    SELECT
        day,
        daily_plays,
        SUM(daily_plays) OVER (ORDER BY day) AS total 
    FROM data
    '''
        
    queries['daily_finished_lobby_runs'] = '''
    WITH data AS (
        SELECT 
            DATE(start_time) AS day,
            COUNT(*) AS daily_plays 
        FROM lobby_runs
        WHERE finished
        GROUP BY day 
    )

    SELECT
        day,
        daily_plays,
        SUM(daily_plays) OVER (ORDER BY day) AS total 
    FROM data
    '''
    
    queries['daily_quick_runs'] = '''
    WITH data AS (
        SELECT 
            DATE(start_time) AS day,
            COUNT(*) AS daily_plays 
        FROM quick_runs
        WHERE start_time IS NOT NULL
        GROUP BY day 
    )

    SELECT
        day,
        daily_plays,
        SUM(daily_plays) OVER (ORDER BY day) AS total 
    FROM data
    '''

    queries['daily_finished_quick_runs'] = '''
    WITH data AS (
        SELECT 
            DATE(start_time) AS day,
            COUNT(*) AS daily_plays 
        FROM quick_runs
        WHERE finished
        GROUP BY day 
    )

    SELECT
        day,
        daily_plays,
        SUM(daily_plays) OVER (ORDER BY day) AS total 
    FROM data
    '''

    queries['daily_created_lobbies'] = '''
    WITH data AS (
        SELECT
            DATE(create_date) AS day,
            COUNT(*) as daily_created_lobbies
        FROM lobbys
        WHERE create_date IS NOT NULL
        GROUP BY day
    )
    
    SELECT
        day,
        daily_created_lobbies,
        SUM(daily_created_lobbies) OVER (ORDER BY day) AS total
    FROM data
    '''

    queries['avg_user_plays'] = '''
    WITH data AS (
        SELECT user_id,
        DATE(start_time) AS day,
        COUNT(*) AS plays
        FROM sprint_runs
        WHERE user_id IS NOT NULL AND start_time IS NOT NULL
        GROUP BY user_id, day
    )

    SELECT
        day,
        AVG(plays) AS "sprint_runs_per_user"
    FROM data
    GROUP BY day
    '''

    queries['avg_user_finished_plays'] = '''
    WITH data AS (
        SELECT user_id,
        DATE(start_time) AS day,
        COUNT(*) AS plays
        FROM sprint_runs
        WHERE user_id IS NOT NULL AND finished
        GROUP BY user_id, day
    )

    SELECT
        day,
        AVG(plays) AS "finished_sprint_runs_per_user"
    FROM data
    GROUP BY day
    '''
    
    queries['avg_user_lobby_plays'] = '''
    WITH data AS (
        SELECT user_id,
        DATE(start_time) AS day,
        COUNT(*) AS plays
        FROM lobby_runs
        WHERE user_id IS NOT NULL AND start_time IS NOT NULL
        GROUP BY user_id, day
    )

    SELECT
        day,
        AVG(plays) AS "lobby_runs_per_user"
    FROM data
    GROUP BY day
    '''

    queries['avg_user_finished_lobby_plays'] = '''
    WITH data AS (
        SELECT user_id,
        DATE(start_time) AS day,
        COUNT(*) AS plays
        FROM lobby_runs
        WHERE user_id IS NOT NULL AND finished
        GROUP BY user_id, day
    )

    SELECT
        day,
        AVG(plays) AS "finished_lobby_runs_per_user"
    FROM data
    GROUP BY day
    '''

    queries['avg_user_quick_plays'] = '''
    WITH data AS (
        SELECT user_id,
        DATE(start_time) AS day,
        COUNT(*) AS plays
        FROM quick_runs
        WHERE user_id IS NOT NULL AND start_time IS NOT NULL
        GROUP BY user_id, day
    )

    SELECT
        day,
        AVG(plays) AS "quick_runs_per_user"
    FROM data
    GROUP BY day
    '''

    queries['avg_user_finished_quick_plays'] = '''
    WITH data AS (
        SELECT user_id,
        DATE(start_time) AS day,
        COUNT(*) AS plays
        FROM quick_runs
        WHERE user_id IS NOT NULL AND finished
        GROUP BY user_id, day
    )

    SELECT
        day,
        AVG(plays) AS "finished_quick_runs_per_user"
    FROM data
    GROUP BY day
    '''

    queries['active_users'] = '''
    WITH data AS (
        SELECT
            COUNT(*) AS plays,
            DATE(end_time) AS day,
            user_id
        FROM sprint_runs
        WHERE user_id IS NOT NULL AND finished
        GROUP BY user_id, day
    )

    SELECT 
        day,
        COUNT(*) AS active_users
    FROM data
    GROUP BY day
    '''
    
    queries['active_lobby_users'] = '''
    WITH data AS (
        SELECT
            COUNT(*) AS plays,
            DATE(end_time) AS day,
            user_id
        FROM lobby_runs
        WHERE user_id IS NOT NULL AND finished
        GROUP BY user_id, day
    )

    SELECT 
        day,
        COUNT(*) AS active_users
    FROM data
    GROUP BY day
    '''

    queries['active_quick_run_users'] = '''
    WITH data AS (
        SELECT
            COUNT(*) AS plays,
            DATE(end_time) AS day,
            user_id
        FROM quick_runs
        WHERE user_id IS NOT NULL AND finished
        GROUP BY user_id, day
    )

    SELECT 
        day,
        COUNT(*) AS active_quick_run_users
    FROM data
    GROUP BY day
    '''


    results = {} 

    db = get_db()
    with db.cursor(cursor=DictCursor) as cursor:
        for name, query in queries.items():
            cursor.execute(query)
            results[name] = cursor.fetchall()
    
    content = gzip.compress(json.dumps(results, cls=CustomJSONEncoder).encode('utf8'), compresslevel=5)
    response = make_response(content)
    response.headers['Content-Length'] = len(content)
    response.headers['Content-Encoding'] = 'gzip'

    return response
