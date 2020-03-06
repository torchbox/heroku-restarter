# Heroku Restarter

A creatively named application to restart Heroku dynos when they're consistently timing out.

Implements a webhook endpoint which when called by a Papertrail alert, will determine which dynos should be restarted and trigger restarts.

Requires `HEROKU_API_KEY` environment variable to be specified.

## Timeouter

An equally poorly named application implementing a web server that responds quickly to `/`, but takes 35 seconds to respond to `/timeout`.
Deploy to Heroku with the included `Dockerfile` for a dumb way to force timeouts.
