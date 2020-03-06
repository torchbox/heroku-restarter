import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler


class TimeouterRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/timeout":
            time.sleep(35)

        self.send_reponse(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("Success")


def run():
    server_address = ("", os.environ.get("PORT"))
    httpd = HTTPServer(server_address, TimeouterRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    run()

