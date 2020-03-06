import os
import json
from urllib.parse import parse_qs
from collections import namedtuple
from http.server import HTTPServer, BaseHTTPRequestHandler
import http.client

HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY")
BASE_HEROKU_API_URL = "https://api.heroku.com"
WHITELISTED_RESTARTABLE_APPS = ["timeouter-test"]
Dyno = namedtuple("Dyno", ["app", "dyno"])


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
    events = body["events"]
    problem_dynos = []
    for event in events:
        problem_dynos.append(parse_dyno_from_event(event))

    # TODO: Do something to sanity check these events and make
    # sure we should actually restart

    for dyno in problem_dynos:
        if dyno.app in WHITELISTED_RESTARTABLE_APPS:
            restart_dyno(dyno)


def parse_dyno_from_event(event):
    """ Return a Dyno by parsing an individual Papertrail event """
    app = event.get("hostname")
    attribute_pairs = event.get("message").split(" ")
    attributes = dict((attr.split("=") + [""])[:2] for attr in attribute_pairs)
    dyno = attributes.get("dyno")
    return Dyno(app=app, dyno=dyno)


def restart_dyno(dyno):
    conn = http.client.HTTPSConnection(BASE_HEROKU_API_URL)
    conn.request(
        "DELETE",
        f"/apps/{dyno.app}/dynos/{dyno.dyno}",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {HEROKU_API_KEY}",
        },
    )


def run():
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, WebhookRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    run()

