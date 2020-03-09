# Heroku Restarter

A creatively named application to restart Heroku dynos when they're consistently timing out.

Implements a webhook endpoint which when called by a Papertrail alert, will determine which dynos should be restarted and trigger restarts.

## Config

Configuration is via environment variables:

- `HEROKU_API_KEY` - API key to access the Heroku API - used for triggering restarts and getting dyno status
- `SLACK_WEBHOOK_URL` - Full URL to the Slack webhook to be called when a dyno is restarted
- `WHITELISTED_APPS` - Comma-separated list of Heroku application names which are allowed to be restarted by this service
- `SECRET_KEY` - A key to be included in the `key` querystring of a request to this endpoint as a simple approach to authorising requests

## Timeouter

An equally poorly named application implementing a web server that responds quickly to `/`, but takes 35 seconds to respond to `/timeout`.
Deploy to Heroku with the included `Dockerfile` for a dumb way to force timeouts.
