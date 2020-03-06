import os
import json
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse
from collections import Counter
from http.server import HTTPServer, BaseHTTPRequestHandler
import http.client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY")
BASE_HEROKU_API_URL = "https://api.heroku.com"
WHITELISTED_RESTARTABLE_APPS = ["timeouter-test"]
EVENT_THRESHOLD = 2  # Only restart if there are at least this many events for a dyno

HEROKU_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/vnd.heroku+json; version=3",
    "Authorization": f"Bearer {HEROKU_API_KEY}",
}


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
                f"Dyno {dyno} should not restart as it is in a 'starting' state"
            )
            return False

        if datetime.strptime(
            status["created_at"], "%Y-%m-%dT%H:%M:%S%z"
        ) >= datetime.now(timezone.utc) - timedelta(minutes=2):
            logger.warning(
                f"Dyno {dyno} should not restart as it was created less than 2 minutes ago"
            )
            return False

        return True

    def restart(self):
        res = do_request(
            "DELETE",
            f"{BASE_HEROKU_API_URL}/apps/{self.app}/dynos/{self.dyno}",
            headers=HEROKU_HEADERS,
        )
        if res.status == 200:
            logger.info("Dyno {dyno} successfully restarted")
            return True

        return False

    def status(self):
        res = do_request(
            "GET",
            f"{BASE_HEROKU_API_URL}/apps/{self.app}/dynos/{self.dyno}",
            headers=HEROKU_HEADERS,
        )
        return json.loads(res.read())


class WebhookRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        payload = parse_qs(post_data)[b"payload"][0]
        parsed_payload = json.loads(payload)
        handle_webhook(parsed_payload)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Success")


def handle_webhook(body):
    """ Given the body of a webhook from Papertrail, determine 
    which dynos are affected and trigger restarts if applicable """
    saved_search_name = body["saved_search"]["name"]
    logger.info(
        f"Received webhook from Papertrail for saved search {saved_search_name}"
    )
    events = body["events"]
    problem_dynos = Counter()
    for event in events:
        dyno = parse_dyno_from_event(event)
        problem_dynos[dyno] += 1

    for dyno, event_count in problem_dynos.items():
        if dyno.app not in WHITELISTED_RESTARTABLE_APPS:
            logger.info(
                f"Dyno {dyno} is timing out but is not whitelisted for restarting"
            )
        elif event_count < EVENT_THRESHOLD:
            logger.info(
                f"Dyno {dyno} is timing out but has not met the restart threshold"
            )
        else:
            if dyno.should_restart():
                logger.info(f"Restarting {dyno}")
                dyno.restart()
                send_slack_message(f"Heroku Restarter has restarted {dyno}")


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
    return res


def run():
    logger.info("Server running")
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, WebhookRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    run()

