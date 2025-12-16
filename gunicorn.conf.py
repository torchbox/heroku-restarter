import gunicorn

# Tell gunicorn to run our app
wsgi_app = "main:app"

# Replace gunicorn's 'Server' HTTP header to avoid leaking info to attackers
gunicorn.SERVER = ""

# Restart gunicorn worker processes every 800-900 requests
max_requests = 800
max_requests_jitter = 100

# Log to stdout
accesslog = "-"

# Time out after 25 seconds (notably shorter than Heroku's)
timeout = 25

# Load app pre-fork to save memory and worker startup time
preload_app = True
