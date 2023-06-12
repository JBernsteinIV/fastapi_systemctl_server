# fastapi_systemctl_server
Continuing FastAPI experience + combining with systemctl and journalctl

Currently this is a Work In Progress (hence the name 'wip.py').

Usage: uvicorn wip:app 

Once running the following routes are supported:
* /service           - Returns a list of all available systemd units of type 'service'.
* /timer             - Returns a list of all available systemd units of type 'timer'.
* /service/{service} - Return a dictionary all properties of the systemd unit. Same as: 'systemctl show <systemd unit>'
* /timer/{timer}     - Same as /service/{service} but for timers.
* /messages/{unit}   - Returns a list of dictionaries containing a message and timestamp since a time. Defaults to 'today'. 
  
Example outputs:
Request URL: http://127.0.0.1:8000/service
Response:
  ```
  [
    ... // Lines omitted for brevity.
    {
    "name": "smartd.service",
    "loaded": true,
    "active": true,
    "state": "running",
    "description": "Self Monitoring and Reporting Technology (SMART) Daemon"
  },
  ]
  ```
 Request URL: http://127.0.0.1:8000/service/smartd
 Response:
  ```
 {
    "Type": "simple",
    "Restart": "no",
    "NotifyAccess": "none",
    "RestartUSec": "100ms",
    "TimeoutStartUSec": "1min 30s",
    ... // Lines omitted for brevity.
  }
  ```
  Request URL: http://127.0.0.1:8000/messages/smartd?since=today
  Response:
  ```
  [
  {
    "timestamp": "2023-06-11T19:47:27",
    "message": "Device: /dev/sda [SAT], SMART Usage Attribute: 190 Airflow_Temperature_Cel changed from 73 to 72"
  },
  {
    "timestamp": "2023-06-11T14:47:27",
    "message": "Device: /dev/sdb [SAT], SMART Usage Attribute: 194 Temperature_Celsius changed from 113 to 112"
  },
  {
    "timestamp": "2023-06-11T14:47:27",
    "message": "Device: /dev/sda [SAT], SMART Usage Attribute: 190 Airflow_Temperature_Cel changed from 74 to 73"
  },
  {
    "timestamp": "2023-06-11T14:17:28",
    "message": "Device: /dev/sdb [SAT], SMART Usage Attribute: 194 Temperature_Celsius changed from 112 to 113"
  },
  {
    "timestamp": "2023-06-11T13:47:27",
    "message": "Device: /dev/sdb [SAT], SMART Usage Attribute: 194 Temperature_Celsius changed from 113 to 112"
  },
  {
    "timestamp": "2023-06-11T10:47:28",
    "message": "Device: /dev/sdb [SAT], SMART Usage Attribute: 194 Temperature_Celsius changed from 121 to 113"
  },
  {
    "timestamp": "2023-06-11T10:47:28",
    "message": "Device: /dev/sda [SAT], SMART Usage Attribute: 190 Airflow_Temperature_Cel changed from 77 to 74"
  },
  ... // Lines omitted for brevity.
]
  ```
