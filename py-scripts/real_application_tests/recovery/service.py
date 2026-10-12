"""Coordinator API for the dedicated private LANforge test network."""
import ipaddress
import json
import logging
import re
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib import request

from .core import Coordinator, RecipeStore, redact
from .lanforge_monitor import LanforgeMonitor


def manager_url(ip, port):
    """Accept only a private LANforge manager IP, never an arbitrary URL."""
    address = ipaddress.ip_address(ip)
    number = int(port)
    if not address.is_private or address.is_loopback or address.is_link_local or not 1 <= number <= 65535:
        raise ValueError("manager must be a private, non-loopback IP and valid port")
    return "http://%s:%d" % (("[" + str(address) + "]") if address.version == 6 else address, number)


class OllamaClient:
    def __init__(self, base_url, model, timeout=12):
        if not base_url or not model:
            raise ValueError("RECOVERY_OLLAMA_BASE_URL and RECOVERY_OLLAMA_MODEL are required")
        self.url = base_url.rstrip("/") + "/api/chat"
        self.model, self.timeout = model, timeout

    def propose(self, failure):
        prompt = ("Return JSON only: {\"selector\": one of permitted selectors, "
                  "\"value\": exact value observed in the UI, \"action\":\"click\"}. "
                  "Choose one uniquely identifiable control for the stated intent. "
                  "Never invent a selector. If ambiguous, return {}. Evidence: "
                  + json.dumps(failure, ensure_ascii=False)[:16000])
        schema = {"type": "object", "properties": {
            "selector": {"type": "string", "enum": ["resourceId", "description", "text", "id", "aria_label"]},
            "value": {"type": "string"}, "action": {"type": "string", "enum": ["click"]}},
            "required": ["selector", "value", "action"], "additionalProperties": False}
        body = {"model": self.model, "stream": False, "think": False, "format": schema,
                "messages": [{"role": "user", "content": prompt}],
                "options": {"temperature": 0, "num_predict": 500, "num_ctx": 4096}}
        req = request.Request(self.url, json.dumps(body).encode(), {"Content-Type": "application/json"})
        # The private Ollama host should not be routed through a process proxy.
        opener = request.build_opener(request.ProxyHandler({}))
        with opener.open(req, timeout=self.timeout) as response:
            answer = json.load(response)["message"]["content"]
        return json.loads(answer)


def serve(host, port, store_path, llm):
    address = ipaddress.ip_address(host)
    if not address.is_private and not address.is_loopback:
        raise ValueError("coordinator must bind to a private or loopback IP")
    coordinator = Coordinator(RecipeStore(store_path), llm)
    monitors = {}
    monitor_lock = threading.Lock()
    log_incidents = deque(maxlen=100)
    log = logging.getLogger("recovery.test_logs")
    log.setLevel(logging.INFO)
    log.propagate = False
    handler = RotatingFileHandler(Path(store_path).resolve().parent / "recovery_test_logs.jsonl",
                                  maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in {"/metrics", "/inventory", "/incidents"}:
                self.send_error(404)
                return
            if self.path == "/metrics":
                body = coordinator.metrics()
            else:
                with monitor_lock:
                    current = list(monitors.items())
                key = "inventory" if self.path == "/inventory" else "incidents"
                body = {url: monitor.snapshot()[key] for url, monitor in current}
                if key == "incidents":
                    with monitor_lock:
                        body["test_logs"] = list(log_incidents)
            data = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 20000:
                    raise ValueError("invalid request size")
                payload = json.loads(self.rfile.read(size))
                if self.path == "/register-manager":
                    url = manager_url(payload["manager_ip"], payload.get("manager_port", 8080))
                    with monitor_lock:
                        if url not in monitors:
                            monitor = LanforgeMonitor(url, store_path)
                            monitors[url] = monitor
                            monitor.start()
                    result = {"registered": True, "manager": url}
                    data = json.dumps(result).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if self.path == "/ingest-log":
                    source = str(payload.get("source", ""))[:120]
                    lines = str(payload.get("text", ""))[-8000:]
                    if not source or not lines:
                        raise ValueError("source and text are required")
                    log.info(json.dumps({"source": redact(source), "text": redact(lines)}))
                    errors = [redact(line)[:500] for line in lines.splitlines()
                              if re.search(r"(?i)\b(error|failed|failure|exception|traceback|timeout)\b", line)]
                    with monitor_lock:
                        for line in errors[-10:]:
                            log_incidents.append({"source": redact(source), "message": line})
                    data = b'{"accepted":true}'
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                failure = payload.get("failure", {})
                allowed = {"youtube"}
                if failure.get("application") not in allowed or failure.get("platform") not in {"android", "windows_chrome"}:
                    raise ValueError("application or platform not authorized")
                if self.path == "/observe":
                    coordinator.propose(failure, "observe")
                    with monitor_lock:
                        log_incidents.append({"source": "ui_hook", "platform": failure["platform"],
                                              "application": failure["application"],
                                              "intent": redact(failure.get("intent", "")),
                                              "category": redact(failure.get("category", ""))})
                    result = {"observed": True, "attempted": False}
                elif self.path == "/propose":
                    result = coordinator.propose(payload["failure"], payload["mode"])
                elif self.path == "/record":
                    result = coordinator.record(payload["failure"], payload["proposal"], payload["result"])
                else:
                    self.send_error(404)
                    return
                data = json.dumps(result).encode()
                self.send_response(200)
            except Exception as exc:
                data = json.dumps({"error": redact(exc)}).encode()
                self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["serve", "promote"])
    parser.add_argument("recipe_id", nargs="?")
    args = parser.parse_args()
    store_path = str(Path(__file__).resolve().parents[1] / "learned_receipe.json")
    if args.command == "promote":
        if not args.recipe_id:
            parser.error("promote requires a recipe ID")
        Coordinator(RecipeStore(store_path)).promote(args.recipe_id)
    else:
        # The AI computer owns this service; workers only call its bounded HTTP API.
        serve("192.168.200.182", 8765, store_path,
              OllamaClient("http://192.168.200.182:11434", "qwen3.8:latest", timeout=60))
