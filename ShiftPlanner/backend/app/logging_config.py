"""JSON formatter for application and Uvicorn logs."""

import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record, suitable for container stdout."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "service": {"name": "shiftplanner-api"},
            "logger": record.name,
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        if record.name == "uvicorn.access" and record.args:
            client, method, path, version, status = record.args
            entry["http"] = {
                "client": str(client),
                "method": str(method),
                "path": str(path),
                "version": str(version),
                "status_code": int(status),
            }
        return json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
