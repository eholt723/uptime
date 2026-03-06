import json
import os
import smtplib
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText

import requests

SITES_FILE = "sites.json"
STATE_FILE = "state.json"

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
ALERT_EMAIL = os.environ["ALERT_EMAIL"]
ALERT_SMS = os.environ["ALERT_SMS"]


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def check_site(site):
    url = site["url"]
    timeout = site.get("timeout", 10)
    retries = site.get("retries", 1)
    check_body = site.get("check_body")
    last_error = None

    for attempt in range(retries):
        if attempt > 0:
            time.sleep(5)
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                if check_body and check_body not in resp.text:
                    last_error = f"status 200 but body check failed (expected: {check_body!r})"
                    continue
                return True, None
            else:
                last_error = f"HTTP {resp.status_code}"
        except requests.exceptions.Timeout:
            last_error = "timeout"
        except requests.exceptions.ConnectionError as e:
            last_error = f"connection error: {e}"
        except Exception as e:
            last_error = f"unexpected error: {e}"

    return False, last_error


def send_alert(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    recipients = [ALERT_EMAIL, ALERT_SMS]
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.sendmail(GMAIL_ADDRESS, recipients, msg.as_string())


def main():
    sites = load_json(SITES_FILE, [])
    state = load_json(STATE_FILE, {})
    state_changed = False
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    for site in sites:
        url = site["url"]
        is_up, error = check_site(site)
        prev_status = state.get(url, "up")

        if is_up:
            print(f"[UP]   {url}")
            if prev_status == "down":
                print(f"       -> recovered, sending BACK UP alert")
                send_alert(
                    f"BACK UP: {url}",
                    f"Site is back up.\n\nURL: {url}\nTime: {now}",
                )
                state[url] = "up"
                state_changed = True
        else:
            print(f"[DOWN] {url} — {error}")
            if prev_status != "down":
                print(f"       -> newly down, sending DOWN alert")
                send_alert(
                    f"DOWN: {url}",
                    f"Site is down.\n\nURL: {url}\nError: {error}\nTime: {now}",
                )
                state[url] = "down"
                state_changed = True

    if state_changed:
        save_json(STATE_FILE, state)
        print("state.json updated")


if __name__ == "__main__":
    main()
