import unittest
from main import Dyno, parse_dyno_from_event

TEST_PAYLOAD = {
    {
        "max_id": "1172555559466221570",
        "min_id": "1172555559466221570",
        "frequency": "minute",
        "saved_search": {
            "id": 47359282,
            "name": "HTTP 5xx Alert",
            "query": '" status=5" -gwripoff -autodiscover.xml',
            "html_edit_url": "https://papertrailapp.com/heroku/go/1795056651?a=app94231806&app=nesta-production&s=edit&search_id=47359282",
            "html_search_url": "https://papertrailapp.com/heroku/go/1795056651?a=app94231806&app=nesta-production&search_id=47359282",
        },
        "events": [
            {
                "id": 1172555559466221570,
                "message": 'at=error code=H12 desc="Request timeout" method=GET path="/timeout" host=timeouter-test.herokuapp.com request_id=6eb9db3e-13ed-41e3-ab78-083ca0c89828 fwd="146.200.199.39" dyno=web.1 connect=0ms service=30001ms status=503 bytes=0 protocol=https\n',
                "program": "heroku/router",
                "source_ip": "54.152.45.17",
                "facility": "",
                "severity": "",
                "hostname": "timeouter-test",
                "source_name": "timeouter-test",
                "source_id": 5174160982,
                "display_received_at": "Mar  6 12:04:12 GMT",
                "received_at": "2020-03-06T12:04:12Z",
            }
        ],
        "counts": None,
        "min_time_at": "2020-03-06T12:04:12Z",
    }
}


class TestAppDynoParser(unittest.TestCase):
    def test_parses_valid_message(self):
        event = TEST_PAYLOAD["events"][0]
        parsed = parse_dyno_from_event(event)
        expected = Dyno(app="app-test", dyno="web.1")
        self.assertEqual(parsed, expected)


if __name__ == "__main__":
    unittest.main()
