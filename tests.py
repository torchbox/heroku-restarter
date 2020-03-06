import unittest
from main import Dyno, parse_dyno_from_event

TEST_PAYLOAD = {
    "events": [
        {
            "id": 7711561783320576,
            "received_at": "2011-05-18T20:30:02-07:00",
            "display_received_at": "May 18 20:30:02",
            "source_ip": "208.75.57.121",
            "source_name": "abc",
            "source_id": 2,
            "hostname": "app-test",
            "program": "CROND",
            "severity": "Info",
            "facility": "Cron",
            "message": 'sock=backend at=error code=H18 desc="Server Request Interrupted" method=POST path="/inc/md5.asp" host=www.nesta.org.uk request_id=32515736-2fd7-46bc-b722-78860110de1d fwd="240e:d9:c200:104:85c5::ec0,172.69.34.65" dyno=web.1 connect=0ms service=44ms status=503 bytes= protocol=https',
        },
        {
            "id": 7711562567655424,
            "received_at": "2011-05-18T20:30:02-07:00",
            "display_received_at": "May 18 20:30:02",
            "source_ip": "208.75.57.120",
            "source_name": "server1",
            "source_id": 19,
            "hostname": "def",
            "program": "CROND",
            "severity": "Info",
            "facility": "Cron",
            "message": "A short event",
        },
    ],
    "saved_search": {
        "id": 42,
        "name": "Important stuff",
        "query": "cron OR server1",
        "html_edit_url": "https://papertrailapp.com/searches/42/edit",
        "html_search_url": "https://papertrailapp.com/searches/42",
    },
    "max_id": 7711582041804800,
    "min_id": 7711561783320576,
    "frequency": "1 minute",
}


class TestAppDynoParser(unittest.TestCase):
    def test_parses_valid_message(self):
        event = TEST_PAYLOAD["events"][0]
        parsed = parse_dyno_from_event(event)
        expected = Dyno(app="app-test", dyno="web.1")
        self.assertEqual(parsed, expected)


if __name__ == "__main__":
    unittest.main()
