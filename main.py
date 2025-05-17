from dotenv import load_dotenv
from icalendar import Calendar
from dateutil.rrule import rrulestr, rruleset
from datetime import datetime, timedelta
import logging
import schedule
import requests
import pytz
import time
import sys
import os

def download_ics_to_bytes(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content

def ics_bytes_to_msg(ics_data, day_range, tz):
    cal = Calendar.from_ical(ics_data)
    now = datetime.now(pytz.utc)
    end = now + timedelta(days=day_range)
    eastern = pytz.timezone(tz)
    events = []
    msg = ""

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get('summary'))
        dtstart = component.decoded('dtstart')

        rrule_field = component.get('rrule')
        if rrule_field:
            rset = rruleset()
            rrule_raw = rrule_field.to_ical().decode()
            rule_text = f"DTSTART:{dtstart.strftime('%Y%m%dT%H%M%SZ')}\nRRULE:{rrule_raw}"
            rule = rrulestr(rule_text, dtstart=dtstart)

            rule = rrulestr(rrule_raw, dtstart=dtstart)
            rset.rrule(rule)

            exdates = component.get('exdate')
            if exdates:
                for ex in exdates.dts:
                    exdt = ex.dt
                    if isinstance(exdt, datetime) and exdt.tzinfo is None:
                        exdt = dtstart.tzinfo.localize(exdt)
                    rset.exdate(exdt)

            for occ in rset.between(now, end, inc=True):
                events.append((summary, occ))
        else:
            if now <= dtstart <= end:
                events.append((summary, dtstart))

    events.sort(key=lambda e: e[1])

    for summary, start in events:
        start_eastern = start.astimezone(eastern)
        date_str = f"{start_eastern.month}/{start_eastern.day}"
        time_str = start_eastern.strftime("%I:%M %p").lstrip("0")
        msg = msg + f"* {date_str} @ {time_str}, {summary}\n"
    
    return msg

def msg_to_discord(msg):
    url = os.getenv("DISCORD_BASEPATH") + "/channels/" + os.getenv("DISCORD_CHANNEL_ID") + "/messages/" + os.getenv("DISCORD_MESSAGE_ID")

    headers = {
        "Authorization": "Bot " + os.getenv("DISCORD_BOT_TOKEN"),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    json_data = {
        "content": msg
    }

    response = requests.patch(url, headers=headers, json=json_data)
    response.raise_for_status()

def main():
    try:
        logger.info("Job executed")
        ics_data = download_ics_to_bytes(os.getenv("CALENDAR_URL"))
        msg = ics_bytes_to_msg(ics_data, int(os.getenv("DAY_RANGE")), os.getenv("TZ"))
        msg_to_discord(msg)
    except Exception as e:
        logger.exception("An error occurred: ")

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

schedule.every(int(os.getenv("FREQ_HOURS_INTERVAL"))).hours.do(main)

while True:
    schedule.run_pending()
    time.sleep(1)
