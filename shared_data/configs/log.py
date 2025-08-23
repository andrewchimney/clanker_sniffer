# ---- unified logging (put at top of acousti_runner.py / whisper_runner.py / etc.) ----
import os, logging, time

# Show UTC timestamps (optional; comment out to use local time)
logging.Formatter.converter = time.gmtime

SERVICE = os.getenv("SERVICE_NAME", "service")

class _ServiceFilter(logging.Filter):
    def filter(self, record):
        record.service = SERVICE
        return True

_fmt = logging.Formatter(
    "%(asctime)s %(service)s %(levelname)s:     %(message)s",  # date + service + padded level + message
    "%Y-%m-%d %H:%M:%S",
)

_handler = logging.StreamHandler()
_handler.setFormatter(_fmt)
_handler.addFilter(_ServiceFilter())

# Replace handlers on uvicorn + root so EVERYTHING uses the same format
for name in ("uvicorn", "uvicorn.error", "uvicorn.access", ""):
    lg = logging.getLogger(name)
    lg.handlers.clear()
    lg.propagate = False
    lg.addHandler(_handler)
    lg.setLevel(logging.INFO)  # use DEBUG if you want more verbosity
# ---- end unified logging ----