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


# ── APScheduler: Auto-Absent Job (master-process only) ───────────────────────
# Running in when_ready means it fires once in the master process before
# workers are forked — so only one scheduler runs regardless of worker count.

_scheduler = None

def when_ready(server):
    """Called once in the master process when gunicorn is ready."""
    global _scheduler
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))

        from dotenv import load_dotenv
        load_dotenv()

        from app import create_app
        _app = create_app(os.environ.get("FLASK_ENV", "development"))

        from apscheduler.schedulers.background import BackgroundScheduler
        from app.routes.admin import run_auto_absent_job
        from app.models import Setting
        from datetime import datetime, date
        import threading

        _state = {"last_run_date": None}
        _lock = threading.Lock()

        def _tick():
            with _lock:
                today = date.today()
                if _state["last_run_date"] == today:
                    return
                if today.weekday() in (5, 6):
                    _state["last_run_date"] = today
                    return
                with _app.app_context():
                    try:
                        settings_dict = Setting.get_all()
                        rules = settings_dict.get("attendance_rules", {})
                        absent_limit = rules.get("absent_limit", "")
                        if not absent_limit:
                            return
                        current_time_str = datetime.now().strftime("%H:%M")
                        if current_time_str > absent_limit:
                            result = run_auto_absent_job()
                            _state["last_run_date"] = today
                            server.log.info(
                                "[AutoAbsent] Job ran — marked=%s skipped=%s",
                                result.get("marked", 0),
                                result.get("skipped", 0),
                            )
                    except Exception as e:
                        server.log.error("[AutoAbsent] tick error: %s", e)

        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(_tick, "interval", minutes=1, id="auto_absent_job")
        _scheduler.start()
        server.log.info("[AutoAbsent] Scheduler started in master process.")

    except ImportError as e:
        server.log.warning("[AutoAbsent] APScheduler not available: %s", e)
    except Exception as e:
        server.log.error("[AutoAbsent] Failed to start scheduler: %s", e)


def on_exit(server):
    """Shut down scheduler cleanly when gunicorn exits."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
