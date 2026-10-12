"""Platform-neutral recovery decisions and durable recipe memory."""
import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 1
MODES = {"disabled", "observe", "replay", "recover"}
SELECTORS = {"android": {"resourceId", "description", "text"},
             "windows_chrome": {"css", "id", "aria_label", "text"}}
_LOCK = threading.RLock()


def classify_exception(exc):
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    if any(term in name + message for term in ("device offline", "disconnected", "invalidsessionid", "adb server")):
        return "disconnected"
    if any(term in name + message for term in ("connectionerror", "network", "dns", "connection refused")):
        return "network"
    if "stale" in name:
        return "stale_element"
    if "notinteractable" in name or "not interactable" in message:
        return "not_interactable"
    if "nosuchelement" in name or "selector" in message and "not found" in message:
        return "selector_not_found"
    if "timeout" in name:
        return "timeout"
    if "clickintercepted" in name or "overlay" in message or "disabled" in message:
        return "blocked_control"
    return "non_ui"


def now():
    return datetime.now(timezone.utc).isoformat()


def redact(value):
    """Keep only bounded UI facts; strip common secrets from free text."""
    value = str(value)[:12000]
    value = re.sub(r"(?i)(token|password|passwd|secret|authorization|cookie)\s*[:=]\s*[^\s<>]+", r"\1=[REDACTED]", value)
    return re.sub(r"(?i)(https?://[^\s?#]+)[?#][^\s<>]+", r"\1?[REDACTED]", value)


def validate_plan(plan, platform):
    if not isinstance(plan, dict) or set(plan) != {"selector", "value", "action"}:
        raise ValueError("plan must contain selector, value, action")
    if plan["selector"] not in SELECTORS.get(platform, ()) or plan["action"] != "click":
        raise ValueError("action or selector is not permitted on this platform")
    if not isinstance(plan["value"], str) or not 1 <= len(plan["value"]) <= 200:
        raise ValueError("invalid selector value")
    return plan


def validate_recipe(recipe):
    required = {"id", "platform", "application", "intent", "category", "state", "plan",
                "successes", "failures", "created_at", "validated_at"}
    if not isinstance(recipe, dict) or not required <= recipe.keys():
        raise ValueError("invalid recipe")
    if recipe["state"] not in {"candidate", "validated", "degraded", "disabled"}:
        raise ValueError("invalid recipe state")
    validate_plan(recipe["plan"], recipe["platform"])
    if not isinstance(recipe["successes"], int) or not isinstance(recipe["failures"], int):
        raise ValueError("invalid counters")
    return recipe


class RecipeStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return {"schema_version": SCHEMA, "recipes": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA or not isinstance(data.get("recipes"), list):
            raise ValueError("unsupported learned_receipe.json schema; original left intact")
        for recipe in data["recipes"]:
            validate_recipe(recipe)
        return data

    def update(self, change):
        with _LOCK:
            data = self.load()
            change(data)
            for recipe in data["recipes"]:
                validate_recipe(recipe)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_name(self.path.name + "." + uuid.uuid4().hex + ".tmp")
            try:
                temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                if self.path.exists():
                    backup = self.path.with_suffix(self.path.suffix + ".bak")
                    backup.write_bytes(self.path.read_bytes())
                os.replace(temp, self.path)
            finally:
                temp.unlink(missing_ok=True)


class Coordinator:
    def __init__(self, store, llm=None, degrade_after=2):
        self.store, self.llm, self.degrade_after = store, llm, degrade_after
        self._metrics_lock = threading.Lock()
        self._metrics = {"ui_failures": 0, "attempts": 0, "validated_successes": 0,
                         "failed_recoveries": 0, "false_recoveries": 0, "recipe_reuses": 0}

    def metrics(self):
        with self._metrics_lock:
            result = dict(self._metrics)
        result["validated_recovery_rate"] = (result["validated_successes"] / result["attempts"]
                                               if result["attempts"] else 0.0)
        return result

    def _count(self, name):
        with self._metrics_lock:
            self._metrics[name] += 1

    def propose(self, failure, mode):
        if mode not in MODES:
            raise ValueError("invalid recovery mode")
        if mode != "disabled":
            self._count("ui_failures")
        if mode in {"disabled", "observe"} or failure.get("category") in {"disconnected", "network", "infrastructure"}:
            return {"attempted": False, "reason": "mode_or_non_ui_failure"}
        platform = failure.get("platform")
        if platform not in SELECTORS:
            raise ValueError("unsupported platform")
        recipes = self.store.load()["recipes"]
        matches = [r for r in recipes if r["state"] == "validated" and all(
            r[k] == failure.get(k) for k in ("platform", "application", "intent", "category"))]
        matches.sort(key=lambda r: (r["successes"] - r["failures"], r["validated_at"] or ""), reverse=True)
        if matches:
            self._count("attempts")
            self._count("recipe_reuses")
            return {"attempted": True, "source": "recipe", "recipe_id": matches[0]["id"], "plan": matches[0]["plan"]}
        if mode != "recover" or self.llm is None:
            return {"attempted": False, "reason": "no_validated_recipe"}
        plan = validate_plan(self.llm.propose(failure), platform)
        fields = {"android": {"resourceId": "resource-id", "description": "content-desc", "text": "text"},
                  "windows_chrome": {"id": "id", "aria_label": "aria_label", "text": "text"}}
        evidence = failure.get("evidence", [])
        if platform == "windows_chrome":
            evidence = evidence.get("controls", []) if isinstance(evidence, dict) else []
        field = fields[platform].get(plan["selector"])
        if not field or not any(isinstance(node, dict) and node.get(field) == plan["value"] for node in evidence):
            raise ValueError("proposed selector is not present in supplied UI evidence")
        self._count("attempts")
        return {"attempted": True, "source": "discovery", "plan": plan}

    def record(self, failure, proposal, result):
        if not proposal.get("attempted"):
            return {"continue": False, "reason": proposal.get("reason")}
        # Workers must report both action and independent postcondition evidence.
        success = result.get("action_succeeded") is True and result.get("postcondition_passed") is True
        self._count("validated_successes" if success else "failed_recoveries")
        if result.get("action_succeeded") is True and not success:
            self._count("false_recoveries")
        if proposal["source"] == "recipe":
            def change(data):
                recipe = next(r for r in data["recipes"] if r["id"] == proposal["recipe_id"])
                recipe["successes" if success else "failures"] += 1
                if success:
                    recipe["validated_at"] = now()
                elif recipe["failures"] >= self.degrade_after:
                    recipe["state"] = "degraded"
                recipe["last_failure"] = None if success else redact(result.get("reason", "validation failed"))
            self.store.update(change)
            return {"continue": success, "recipe_id": proposal["recipe_id"], "validated": success}
        if success:
            recipe = {"id": uuid.uuid4().hex, "platform": failure["platform"],
                      "application": failure["application"], "intent": failure["intent"],
                      "category": failure["category"], "state": "candidate",
                      "plan": proposal["plan"], "successes": 1, "failures": 0,
                      "created_at": now(), "validated_at": now(), "last_failure": None}
            def change(data):
                existing = next((item for item in data["recipes"] if item["state"] == "candidate"
                                 and all(item[key] == recipe[key] for key in
                                         ("platform", "application", "intent", "category", "plan"))), None)
                if existing:
                    existing["successes"] += 1
                    existing["validated_at"] = now()
                    recipe["id"] = existing["id"]
                else:
                    data["recipes"].append(recipe)
            self.store.update(change)
            return {"continue": True, "recipe_id": recipe["id"], "validated": True, "trusted": False}
        return {"continue": False, "validated": False}

    def promote(self, recipe_id):
        def change(data):
            recipe = next(r for r in data["recipes"] if r["id"] == recipe_id)
            if recipe["state"] != "candidate" or recipe["successes"] < 1 or not recipe["validated_at"]:
                raise ValueError("candidate has no successful validation")
            recipe["state"] = "validated"
        self.store.update(change)
