"""Small recovery hook imported by an existing Android test; no agent process."""
import json
import time
import xml.etree.ElementTree as ET
from urllib import request

from .core import MODES, redact, validate_plan


def wait_for_postcondition(verify, seconds=3):
    deadline = time.monotonic() + seconds
    while True:
        if verify():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.2)


class CoordinatorClient:
    def __init__(self, url=None, timeout=8):
        self.url = (url or "http://192.168.200.182:8765").rstrip("/")
        self.timeout = timeout

    def call(self, route, payload):
        if not self.url.startswith(("http://192.168.200.182:", "http://127.0.0.1:", "http://localhost:")):
            raise ValueError("coordinator URL must be the configured AI computer or loopback")
        req = request.Request(self.url + route, json.dumps(payload).encode(),
                              {"Content-Type": "application/json"})
        timeout = 65 if route == "/propose" else self.timeout
        opener = request.build_opener(request.ProxyHandler({}))
        with opener.open(req, timeout=timeout) as response:
            return json.load(response)


def register_manager(manager_ip, manager_port):
    """Tell the central coordinator which LANforge manager this test uses."""
    return CoordinatorClient(timeout=3).call(
        "/register-manager", {"manager_ip": manager_ip, "manager_port": manager_port})


def forward_test_log(source, text):
    """Best-effort log copy; the normal LANforge report remains authoritative."""
    return CoordinatorClient(timeout=3).call(
        "/ingest-log", {"source": source[:120], "text": redact(text[-8000:])})


class AndroidAdapter:
    def __init__(self, device):
        self.device = device

    def evidence(self):
        root = ET.fromstring(self.device.dump_hierarchy(compressed=False))
        nodes = []
        for node in root.iter("node"):
            attrs = {key: redact(node.attrib.get(key, "")) for key in
                     ("resource-id", "content-desc", "text", "class", "clickable", "enabled")}
            if attrs["resource-id"] or attrs["content-desc"] or attrs["text"]:
                nodes.append(attrs)
        return nodes[:150]

    def execute(self, plan, verify):
        validate_plan(plan, "android")
        key = plan["selector"]
        obj = self.device(**{key: plan["value"]})
        # A unique enabled target and a checked postcondition are mandatory.
        if obj.count != 1 or not obj.info.get("enabled", False):
            return {"action_succeeded": False, "postcondition_passed": False, "reason": "ambiguous or disabled target"}
        if verify():
            return {"action_succeeded": True, "postcondition_passed": True, "reason": "already satisfied"}
        obj.click()
        return {"action_succeeded": True, "postcondition_passed": wait_for_postcondition(verify)}


def recover(adapter, platform, application, intent, category, verify, mode=None, client=None):
    mode = mode or "recover"
    if mode not in MODES or mode == "disabled":
        return {"continue": False, "attempted": False}
    failure = {"platform": platform, "application": application, "intent": intent,
               "category": category, "evidence": adapter.evidence()}
    if mode == "observe":
        try:
            (client or CoordinatorClient(timeout=3)).call("/observe", {"failure": failure})
        except Exception:
            pass  # Observe mode must preserve the original test outcome.
        return {"continue": False, "attempted": False, "evidence": failure}
    client = client or CoordinatorClient()
    proposal = client.call("/propose", {"failure": failure, "mode": mode})
    if not proposal.get("attempted"):
        return {"continue": False, **proposal}
    result = adapter.execute(proposal["plan"], verify)
    return client.call("/record", {"failure": failure, "proposal": proposal, "result": result})
