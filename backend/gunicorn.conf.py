# ==============================================================================
# Gunicorn Production Configuration
# GeoFace Faculty Authentication System
# ==============================================================================

import multiprocessing
import os

worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gevent")

if worker_class == "gevent":
    try:
        from gevent import monkey
        monkey.patch_all()
    except ImportError:
        pass


# Worker count: 2 × CPU_count + 1  (standard formula for I/O-bound apps)
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker class — use gevent for high concurrency (pip install gevent)
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gevent")

# Each gevent worker can handle many connections
worker_connections = int(os.environ.get("GUNICORN_WORKER_CONNECTIONS", "1000"))

# Give face-recognition processing time
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 30

# Bind
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:5000")

# Logging
accesslog = "-"               # stdout
errorlog = "-"                # stderr
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# Keep-alive
keepalive = 5

# Preload app for copy-on-write memory efficiency
preload_app = False

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
