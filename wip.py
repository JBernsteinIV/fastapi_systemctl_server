from datetime import datetime
import json
import subprocess
import shutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Union
from pydantic import BaseModel

app = FastAPI()

origins = [
    'http://localhost:27017', # To set up with MongoDB.
    'http://localhost:3000'   # To set up with React front-end.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins     = origins,
    allow_credentials = True,
    allow_methods     = ['*'],
    allow_headers     = ['*'],
)

@app.get("/")
def read_root():
    return None

""" Internal function. Attempt to query systemctl. Return list of valid types if incorrect type is passed in."""
def _internal_systemctl_get_units(unit_type: str) -> List[str]:
    results = []
    # Get the path to systemctl if in a non-standard location.
    systemctl_path = shutil.which('systemctl')
    try:
        command = [systemctl_path,'list-units',f'--type={unit_type}', '--no-legend','--all']
        output  = subprocess.check_output(command).decode('utf-8').split('\n')
        for line in output:
            # Remove non-alphanumeric characters.
            for character in line:
                if not character.isalpha():
                    line.replace(character,'')
            line = line.split()
            template = {
                'name'        : line[0],
                'loaded'      : line[1].lower() == 'loaded',
                'active'      : line[2].lower() == 'active',
                'state'       : line[3],
                'description' : " ".join(line[4:])
            }
            results.append(template)
    except subprocess.CalledProcessError:
        help_options = [systemctl_path, 'list-units','--type=help']
        output       = subprocess.check_output(help_options).decode('utf-8').split('\n')
        for line in output:
            line = line.strip()
            if 'Available' in line or line == '':
                continue
            results.append(line.strip())
    finally:
        return results
""" Internal function. Get the available properties that can be queried or set by systemd. Return None if unit is not found."""
def _internal_get_properties(unit_name) -> Union[dict, None]:
    systemctl_path = shutil.which('systemctl')
    MAGIC_NUM_FOR_INF = 18446744073709551615
    command = [systemctl_path,'show',unit_name]
    try:
        output = subprocess.check_output(command).decode('utf-8').split('\n')
        template = {}
        for line in output:
            key = line.split('=')[0]
            if key == 'LoadError':
                return None
            if key == '':
                continue
            val = "".join(line.split('=')[1:])
            if str.isdigit(val):
                val = int(val)
                if val == MAGIC_NUM_FOR_INF:
                    val = "infinity"
            template[key] = val
        return template
    except subprocess.CalledProcessError:
        return None
""" 
    Internal function. Call journalctl to get the logs of the specified unit. 
    Defaults to logs since 1 hour ago and last 50 logs.
    Return None if unit not found or no logs were found.
"""
def _internal_journalctl_get_messages(unit_name: str, since="1 hour ago", limit=10) -> List[dict]:
    if since == None:
        since = "1 hour ago"
    if limit == None or limit <= 0:
        limit = 10
    journalctl_path = shutil.which('journalctl')
    command = [journalctl_path,f'--unit={unit_name}','--output=json',f"--since={since}", '--reverse']
    try:
        output   = subprocess.check_output(command).decode('utf-8')
        messages = []
        for message in output.split('\n'):
            template = {}
            if message == '':
                continue
            msg = json.loads(message)
            if '__REALTIME_TIMESTAMP' in msg.keys() and 'MESSAGE' in msg.keys():
                # Convert the timestamp in microseconds to seconds.
                timestamp = int(msg.get('__REALTIME_TIMESTAMP')) // 1000000
                template['timestamp'] = datetime.fromtimestamp(timestamp)
                template['message']   = msg.get('MESSAGE')
            if len(template.keys()) > 0:
                messages.append(template)
        return messages[:limit]
    except subprocess.CalledProcessError:
        return None

""" Returns a list of all systemd units of type 'service'."""
@app.get("/service")
def get_services():
    services = _internal_systemctl_get_units(unit_type='service')
    return services

""" Returns a list of all systemd units of type 'timer'."""
@app.get("/timer")
def get_timers():
    timers = _internal_systemctl_get_units(unit_type='timer')
    return timers

# Scan systemctl for the current state of this service.
@app.get("/service/{service}")
def check_service(service: str):
    properties = _internal_get_properties(unit_name=service)
    return properties

@app.get("/timer/{timer}")
def get_timers(timer: str):
    if 'timer' not in timer:
        if '.' in timer:
            timer = timer.split('.')[0]
        timer += '.timer'
        properties = _internal_get_properties(unit_name=timer)
        return properties

@app.get("/messages/{unit}")
def get_messages(unit: str, since: Optional[str] = None, limit: Optional[int] = None) -> Union[List[dict],None]:
    messages = _internal_journalctl_get_messages(unit_name=unit, since=since, limit=limit)
    if len(messages) > 0:
        return messages
    else:
        if since == None:
            since = "today"
        return [f"No messages found since {since}"]