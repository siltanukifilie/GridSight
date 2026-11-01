"""Small, stateless public demo. Render terminates HTTPS before this server."""
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "8050")
workers = 1
threads = 1
worker_class = "sync"
timeout = 120
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 100
# No request bodies, project identifiers, IP addresses or query strings in access logs.
accesslog = None
errorlog = "-"
loglevel = "warning"
