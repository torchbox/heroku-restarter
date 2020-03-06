import json
from urllib.parse import parse_qs
from collections import namedtuple
from http.server import HTTPServer, BaseHTTPRequestHandler
import http.client

BASE_HEROKU_API_URL = "https://api.heroku.com"
Dyno = namedtuple("Dyno", ["app", "dyno"])


class WebhookRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        parse_webhook_body(parse_qs(post_data)["payload"])
        self.send_reponse(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("Success")


def parse_webhook_body(body):
    print(body)
    body_data = json.loads(body)
    events = body_data["events"]
    problem_dynos = []
    for event in events:
        problem_dynos.append(parse_dyno_from_event(event))


def parse_dyno_from_event(event):
    app = event.get("hostname")
    attribute_pairs = event.get("message").split(" ")
    attributes = dict((attr.split("=") + [""])[:2] for attr in attribute_pairs)
    dyno = attributes.get("dyno")
    return Dyno(app=app, dyno=dyno)


def restart_dyno(dyno: Dyno):
    conn = http.client.HTTPSConnection(BASE_HEROKU_API_URL)
    conn.request(
        "DELETE",
        f"/apps/{dyno.app}/dynos/{dyno.dyno}",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/vnd.heroku+json; version=3",
        },
    )


def run():
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, WebhookRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    run()

