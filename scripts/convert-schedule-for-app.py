#!/usr/bin/env python3

"""
Convert the schedule JSON used on website to adapted format for app.
source: https://github.com/paug/android-makers-2019/blob/master/data/database/schedule.json

python3.10 is needed for this script. On Mac os you can install it with `brew install python@3.10`.

This script will take data/database/rooms.json and data/database/schedule.json files and
transform them into data/database/schedule-app.json.

To run it, simply call `./scripts/convert-schedule-for-app.py`.
"""

import json

from datetime import timedelta, datetime, tzinfo, timezone
import zoneinfo
import os

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(FILE_PATH, "..", "data", "database")

input_rooms_raw = os.path.join(DATABASE_PATH, "rooms.json")
input_schedule_raw = os.path.join(DATABASE_PATH, "schedule.json")
output_schedule_app = os.path.join(DATABASE_PATH, "schedule-app.json")

""" Part that are needed to be updated each year, according to the days and the rooms. """
room_ids = ["Moebius", "Blin", "2.02", "2.04"]
days = ["2022-04-25", "2022-04-26"]
""" End of the year editable part """

talks = []
rooms = []

def convertDate(datetime_str):
    date_time_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
    eu_timezone = zoneinfo.ZoneInfo('Europe/Paris')
    return date_time_obj.astimezone(tz=eu_timezone).isoformat()

def extractTalks(day_str, timeslots):
    for slot in timeslots:
        start_date_string = "{} {}".format(day_str, slot["startTime"])
        end_date_string = "{} {}".format(day_str, slot["endTime"])

        sessions = slot["sessions"]
        if (len(sessions) == 1):
            talk = {}

            items = sessions[0]["items"]
            talk["startDate"] = convertDate(start_date_string)
            talk["endDate"] = convertDate(end_date_string)
            talk["roomId"] = "all"
            talk["sessionId"] = items[0]
            talks.append(talk)
        if (len(sessions) == 4 or len(sessions) == 5):
            for session in sessions:
                items = session["items"]
                session_index = sessions.index(session)

                if (len(items) > 0):
                    talk = {}
                    talk["startDate"] = convertDate(start_date_string)
                    talk["roomId"] = room_ids[session_index]
                    talk["sessionId"] = items[0]
                    if (session.get("extend") != None):
                        slot_index = timeslots.index(slot)
                        extend_slot = timeslots[slot_index + session["extend"] - 1]
                        extend_end_date_string = "{} {}".format(day_str, extend_slot["endTime"])
                        talk["endDate"] = convertDate(extend_end_date_string)
                    else:
                        talk["endDate"] = convertDate(end_date_string)

                    talks.append(talk)

def extractRooms(rooms_raw):
    for room_raw_id in rooms_raw.keys():
        room_raw = rooms_raw[room_raw_id]
        room = {
            "roomId": room_ids[int(room_raw_id)],
            "roomName": room_raw["name"],
            "infos": room_raw["level"],
            "capacity": room_raw["capacity"]
        }
        rooms.append(room)

with open(input_schedule_raw) as json_data:
    schedule = json.load(json_data)
    day_1 = schedule[days[0]]
    day_2 = schedule[days[1]]

    timeslots_day_1 = day_1["timeslots"]
    timeslots_day_2 = day_2["timeslots"]

    extractTalks(days[0], timeslots_day_1)
    extractTalks(days[1], timeslots_day_2)

with open(input_rooms_raw) as json_data:
    rooms_raw = json.load(json_data)
    extractRooms(rooms_raw)

with open(output_schedule_app, 'w') as outfile:
    schedule_app = {
        "slots": {
            "all": talks
        },
        "rooms": {
            "allRooms": rooms
        }
    }
    json.dump(schedule_app, outfile, sort_keys=True, indent=2)
    print("Schedule for app correctly written in " + output_schedule_app)
