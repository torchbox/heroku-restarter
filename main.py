import http.client
import json
import logging
import os
import fnmatch
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY")
BASE_HEROKU_API_URL = "https://api.heroku.com"
ALLOWLIST_APP_PATTERNS = os.environ.get("ALLOWLIST_APP_PATTERNS", "").split(",")
SECRET_KEY = os.environ.get(
    "SECRET_KEY", ""
)  # Key used to authorise requests to this endpoint
EVENT_THRESHOLD = 2  # Only restart if there are at least this many events for a dyno

HEROKU_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/vnd.heroku+json; version=3",
    "Authorization": f"Bearer {HEROKU_API_KEY}",
}


class RequestError(Exception):
    def __init__(self, *args, **kwargs):
        self.response = kwargs.pop("response")
        self.request_url = kwargs.pop("request_url")
        super().__init__(*args, **kwargs)


@dataclass(eq=True, frozen=True)
class Dyno:
    app: str
    dyno: str

    def __str__(self):
        return f"{self.app} {self.dyno}"

    def should_restart(self):
        status = self.status()
        if status["state"] == "starting":
            logger.warning(
                f"Dyno {self} should not restart as it is in a 'starting' state"
            )
            return False

        if datetime.strptime(
            status["created_at"], "%Y-%m-%dT%H:%M:%S%z"
        ) >= datetime.now(timezone.utc) - timedelta(minutes=2):
            logger.warning(
                f"Dyno {self} should not restart as it was created less than 2 minutes ago"
            )
            return False

        heroku_status = json.loads(
            do_request("GET", "https://status.heroku.com/api/v4/current-status").read()
        )
        for system in heroku_status["status"]:
            if system["system"] == "Apps" and system["status"] == "red":
                logger.warning(
                    f"Dyno {self} should not restart as there is an ongoing Heroku outage"
                )
                return False

        return True

    def restart(self):
        res = do_request(
            "DELETE",
            f"{BASE_HEROKU_API_URL}/apps/{self.app}/dynos/{self.dyno}",
            headers=HEROKU_HEADERS,
        )
        logger.info("Dyno {dyno} successfully restarted")

    def status(self):
        res = do_request(
            "GET",
            f"{BASE_HEROKU_API_URL}/apps/{self.app}/dynos/{self.dyno}",
            headers=HEROKU_HEADERS,
        )
        return json.loads(res.read())


class WebhookRequestHandler(BaseHTTPRequestHandler):
    def send_html_response(self, status, body):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        url_parts = urlparse(self.path)
        querystring = parse_qs(url_parts.query)
        if querystring.get("key", [])[0] != SECRET_KEY:
            self.send_html_response(403, b"Incorrect key")
            return

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        payload = parse_qs(post_data)[b"payload"][0]
        parsed_payload = json.loads(payload)
        handle_webhook(parsed_payload)
        self.send_html_response(200, b"Success")


def app_is_in_allowlist(app):
    """ Check whether the given app name matches a pattern
    in the allowlist """
    for pattern in ALLOWLIST_APP_PATTERNS:
        if fnmatch.fnmatch(app, pattern):
            return True
    return False


def handle_webhook(body):
    """ Given the body of a webhook from Papertrail, determine 
    which dynos are affected and trigger restarts if applicable """
    saved_search_name = body["saved_search"]["name"]
    logger.info(
        f"Received webhook from Papertrail for saved search {saved_search_name}"
    )
    events = body["events"]
    problem_dynos = Counter(parse_dyno_from_event(event) for event in events)

    for dyno, event_count in problem_dynos.items():
        if not app_is_in_allowlist(dyno.app):
            logger.info(
                f"Dyno {dyno} is timing out but does not match an allowlisted pattern restarting"
            )
        elif event_count < EVENT_THRESHOLD:
            logger.info(
                f"Dyno {dyno} is timing out but has not met the restart threshold"
            )
        else:
            try:
                if dyno.should_restart():
                    logger.info(f"Restarting {dyno}")
                    dyno.restart()
                    send_slack_message(f"Heroku Restarter has restarted {dyno}")
            except RequestError as e:
                logger.error(
                    f"While restarting {dyno}, request to {e.request_url} returned status {e.response.status}: {e}"
                )


def parse_dyno_from_event(event):
    """ Return a Dyno by parsing an individual Papertrail event """
    app = event.get("hostname")
    attribute_pairs = event.get("message").split(" ")
    attributes = dict((attr.split("=") + [""])[:2] for attr in attribute_pairs)
    dyno = attributes.get("dyno")
    return Dyno(app=app, dyno=dyno)


def send_slack_message(message):
    do_request(
        "POST",
        SLACK_WEBHOOK_URL,
        body=json.dumps({"text": message}),
        headers={"Content-type": "application/json"},
    )


def do_request(method, url, **kwargs):
    url_parts = urlparse(url)
    conn = http.client.HTTPSConnection(url_parts.netloc)
    conn.request(method, url_parts.path, **kwargs)
    res = conn.getresponse()
    if res.status > 299:
        raise RequestError(res.read().decode("utf-8"), response=res, request_url=url)

    return res


def run():
    logger.info("Server running")
    server_address = ("", int(os.environ.get("PORT", "8000")))
    httpd = HTTPServer(server_address, WebhookRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    run()
