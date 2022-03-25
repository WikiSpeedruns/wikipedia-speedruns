from flask import Blueprint, jsonify
from pymysql.cursors import DictCursor

from util.decorators import check_admin
from db import get_db

stats_api = Blueprint("stats", __name__, url_prefix="/api/stats")

@check_admin
@stats_api.get("/totals")
def get_total_stats():
    queries = []
    queries.append("SELECT COUNT(*) AS users_total FROM users")
    queries.append("SELECT COUNT(*) AS sprints_total FROM sprint_runs")
    queries.append("SELECT COUNT(*) AS sprints_finished FROM sprint_runs WHERE path IS NOT NULL")

    results = {}

    db = get_db()
    with db.cursor(cursor=DictCursor) as cursor:
        for query in queries:
            cursor.execute(query)
            results.update(cursor.fetchall()[0])
        return jsonify(results)


@check_admin
@stats_api.get("/weekly")
def get_weekly_stats():
    queries = {}
    queries['users_weekly'] = '''
    WITH data AS (
        SELECT 
            YEAR(join_date) AS year, 
            DATE_FORMAT(join_date, '%b %e') AS week, 
            COUNT(*) AS weekly_users
        FROM users
        GROUP BY year, week
    )

    SELECT
        year,
        week,
        weekly_users,
        SUM(weekly_users) OVER (ORDER BY week) AS cum_total
    FROM data
    '''
    queries['plays_weekly'] = '''
    SELECT 
        YEAR(start_time) AS year, 
        DATE_FORMAT(start_time, '%b %e') AS week, 
        COUNT(*) AS weekly_plays 
    FROM sprint_runs
    GROUP BY year, week
    '''
    queries['finished_plays_weekly'] = '''
    SELECT 
        YEAR(start_time) AS year, 
        DATE_FORMAT(start_time, '%b %e') AS week, 
        COUNT(*) AS weekly_plays 
    FROM sprint_runs
    WHERE path IS NOT NULL
    GROUP BY year, week
    '''
    
    results = {}

    db = get_db()
    with db.cursor(cursor=DictCursor) as cursor:
        for name, query in queries.items():
            cursor.execute(query)
            results[name] = cursor.fetchall()
        return jsonify(results)

@check_admin
@stats_api.get("/daily")
def get_daily_stats():
    queries = {}
    queries['avg_unique_user_plays'] = '''
    SELECT 
        day, 
        year,
        AVG(plays) AS "plays_per_user"
    FROM (
        SELECT 
            user_id, 
            DATE_FORMAT(start_time, '%b %e') AS day,
            YEAR(start_time) as year,
            COUNT(*) AS plays
        FROM sprint_runs 
        GROUP BY user_id, day, year
    ) a
    group by day, year
    '''

    results = {} 

    db = get_db()
    with db.cursor(cursor=DictCursor) as cursor:
        for name, query in queries.items():
            cursor.execute(query)
            results[name] = cursor.fetchall()
        return jsonify(results)