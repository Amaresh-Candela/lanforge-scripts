"""Read-only LANforge discovery and error collection on the AI computer."""
import json
import logging
import re
import sys
import threading
import time
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .core import redact

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def records(payload, key):
    """LANforge list endpoints return both keyed dictionaries and lists."""
    value = payload.get(key, []) if isinstance(payload, dict) else []
    if isinstance(value, dict):
        value = [value] if any(k in value for k in ("name", "entity id", "status")) else [{name: item} for name, item in value.items()]
    result = []
    for entry in value if isinstance(value, list) else []:
        if not isinstance(entry, dict):
            continue
        if len(entry) == 1 and isinstance(next(iter(entry.values())), dict):
            name, item = next(iter(entry.items()))
            result.append({"name": name, **item})
        else:
            result.append(entry)
    return result


class LanforgeMonitor:
    PATHS = (("resources", "/resource/all", "resources"),
             ("adb", "/adb/", "devices"),
             ("ports", "/ports/all/", "interfaces"),
             ("generic", "/generic/", "endpoints"),
             ("events", "/events/last/50", "events"),
             ("alerts", "/alerts/last/50", "alerts"))

    def __init__(self, url, store_path, interval=15, query=None):
        self.url, self.interval, self.query = url, interval, query
        self.inventory = {"resources": [], "adb": [], "ports": [], "generic": []}
        self.incidents = deque(maxlen=100)
        self.seen = set()
        self.lock = threading.Lock()
        log_path = Path(store_path).resolve().parent / "recovery_monitor.jsonl"
        self.logger = logging.getLogger("recovery.lanforge." + str(id(self)))
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        if query is None:
            handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    def _query(self):
        if self.query is None:
            from lanforge_client.lanforge_api import LFSession
            session = LFSession(lfclient_url=self.url, connection_timeout_sec=4,
                                stream_errors=False,
                                require_session=False, exit_on_error=False)
            self.query = session.get_query()
        return self.query

    def poll_once(self):
        query = self._query()
        fetched = {}
        for label, path, key in self.PATHS:
            try:
                response = query.get_as_json(url=path, wait_sec=0,
                                             request_timeout_sec=4, max_timeout_sec=4)
                if response is None:
                    raise ConnectionError("LANforge API returned no response for " + path)
                fetched[label] = records(response, key)
            except Exception as exc:
                # A missing optional endpoint must not stop resource discovery.
                fetched[label] = []
                self.logger.warning(json.dumps({"kind": "lanforge_poll_error", "path": path,
                                                "message": redact(exc)}))
        snapshot = {
            "resources": [{key: redact(item.get(key, "")) for key in
                           ("name", "eid", "hostname", "ctrl-ip", "user", "state", "type")}
                          for item in fetched["resources"]],
            "adb": [{key: redact(item.get(key, "")) for key in
                     ("name", "device", "model", "type", "phantom", "unauth", "timed-out", "resource-id")}
                    for item in fetched["adb"]],
            "ports": [{key: redact(item.get(key, "")) for key in
                       ("name", "entity id", "port", "device", "status", "ip", "port type")}
                      for item in fetched["ports"]],
            "generic": [{key: redact(item.get(key, "")) for key in ("name", "type", "status")}
                        for item in fetched["generic"]],
        }
        incidents = []
        for group in ("events", "alerts"):
            for item in fetched[group]:
                message = str(item.get("event description") or item.get("event") or "")
                if re.search(r"(?i)\b(error|failed|failure|timeout|disconnect|phantom)\b", message):
                    incidents.append({"source": group, "id": str(item.get("id", "")),
                                      "message": redact(message)})
        for item in fetched["generic"]:
            message = str(item.get("last results", ""))
            if re.search(r"(?i)\b(error|failed|failure|timeout|exception)\b", message):
                incidents.append({"source": "generic", "id": str(item.get("name", "")),
                                  "message": redact(message)})
        with self.lock:
            self.inventory = snapshot
            for incident in incidents:
                marker = (incident["source"], incident["id"], incident["message"])
                if marker not in self.seen:
                    self.seen.add(marker)
                    self.incidents.append(incident)
                    self.logger.info(json.dumps({"kind": "lanforge_incident", **incident}))
            if len(self.seen) > 1000:
                self.seen = {(i["source"], i["id"], i["message"]) for i in self.incidents}
        return self.snapshot()

    def snapshot(self):
        with self.lock:
            return {"inventory": self.inventory, "incidents": list(self.incidents)}

    def run_forever(self):
        while True:
            try:
                self.poll_once()
            except Exception as exc:
                self.query = None
                self.logger.warning(json.dumps({"kind": "lanforge_poll_error", "message": redact(exc)}))
            time.sleep(self.interval)

    def start(self):
        threading.Thread(target=self.run_forever, daemon=True, name="lanforge-monitor").start()
