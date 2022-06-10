import pymysql
from flask import Flask, jsonify, request, Blueprint, session

import json
import datetime

from db import get_db
from pymysql.cursors import DictCursor

from util.decorators import check_admin, check_request_json
from wikispeedruns import prompts

sprint_api = Blueprint('sprints', __name__, url_prefix='/api/sprints')


### Prompt Management Endpoints
@sprint_api.post('/')
@check_admin
@check_request_json({"start": str, "end": str})
def create_prompt():
    #print(request.json)

    start = request.json.get('start')
    end = request.json.get('end')

    if (start is None or end is None): return "Invalid Request", 400

    id = prompts.add_sprint_prompt(start, end)
    return f"Created prompt {id}", 200


@sprint_api.delete('/<id>')
@check_admin
def delete_prompt(id):
    try:
        if prompts.delete_prompt(id, "sprint"):
            return "Prompt deleted!", 200
        else:
            return "Could not delete prompt, may already have run(s)", 400
    except prompts.PromptNotFoundError:
        return "Prompt {id} not found!", 404

@sprint_api.patch('/<id>')
@check_admin
@check_request_json({"startDate": str, "endDate": str, "rated": bool})
def set_prompt_active_time(id):
    '''
    Change whether a prompt is public, daily, or unsued

    Example json inputs
    {
        "startDate": "2020-10-20"      // <---- ISO Date
        "endDate": "2020-10-20"
        "rated": true
    }

    {
        "startDate": "2020-10-20"      // <---- ISO Date
        "endDate": "2020-10-27"
        "rated": false
    }

    '''

    try:
        start_date = datetime.date.fromisoformat(request.json.get("startDate", ""))
        end_date = datetime.date.fromisoformat(request.json.get("endDate", ""))
        rated = request.json.get("rated")
    except (KeyError, ValueError) as e:
        return f"Invalid input", 400


    try:

        if (rated):
            prompts.set_ranked_daily_prompt(id, start_date)
            return f"Set prompt {id} as daily ranked for {start_date}", 200

        else:
            prompts.set_prompt_time(id, "sprint", start_date, end_date)
            return f"Set prompt {id} active from {start_date} to {end_date}", 200

    except prompts.PromptNotFoundError:
        return "Prompt {id} not found!", 404


### Prompt Search Endpoints
@sprint_api.get('/managed')
@check_admin
def get_managed_prompts():
    return jsonify(prompts.get_managed_prompts("sprint"))

@sprint_api.get('/active')
def get_active_prompts():
    return jsonify(prompts.get_active_prompts("sprint", user_id=session.get("user_id")))

@sprint_api.get('/archive')
def get_archive_prompts():
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        sprints, num_prompts = prompts.get_archive_prompts("sprint",
            offset=offset,
            limit=limit,
            user_id=session.get("user_id")
        )

        return jsonify({
            "prompts": sprints,
            "numPrompts": num_prompts
        })

    except ValueError:
        return "Invalid limit or offset", 400

### Specific prompt endpoints

@sprint_api.get('/<int:id>')
def get_prompt(id):
    prompt = prompts.get_prompt(id, "sprint", session.get("user_id"))

    if (prompt is None):
        return "Prompt does not exist", 404

    if (session.get("admin")):
        return prompt

    if not prompt["used"]:
        return "Prompt does not exist", 404

    if not prompt["available"]:
        return "Prompt not yet available", 401

    if prompt["rated"] and prompt["active"] and "user_id" not in session:
        return "You must be logged in to play this daily prompt", 401

    return prompt
