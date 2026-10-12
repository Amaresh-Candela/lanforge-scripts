import json
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from .core import Coordinator, RecipeStore, classify_exception
from .test_hook import AndroidAdapter, recover
from .service import OllamaClient
from . import test_hook, service
from .lanforge_monitor import LanforgeMonitor


FAILURE = {"platform": "android", "application": "youtube", "intent": "enable_stats_for_nerds",
           "category": "selector_not_found", "evidence": [{"text": "Stats for nerds"}]}
PLAN = {"selector": "text", "value": "Stats for nerds", "action": "click"}


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def propose(self, failure):
        self.calls += 1
        return PLAN


class MemoryStore:
    def __init__(self):
        self.data = {"schema_version": 1, "recipes": []}
        self.lock = threading.RLock()

    def load(self):
        with self.lock:
            return json.loads(json.dumps(self.data))

    def update(self, change):
        with self.lock:
            change(self.data)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.llm = FakeLLM()
        self.coordinator = Coordinator(self.store, self.llm)

    def test_discovery_candidate_promotion_and_replay(self):
        proposal = self.coordinator.propose(FAILURE, "recover")
        self.assertEqual(proposal["source"], "discovery")
        result = self.coordinator.record(FAILURE, proposal, {"action_succeeded": True, "postcondition_passed": True})
        self.assertTrue(result["continue"])
        self.assertEqual(self.store.load()["recipes"][0]["state"], "candidate")
        self.assertFalse(self.coordinator.propose(FAILURE, "replay")["attempted"])
        self.coordinator.promote(result["recipe_id"])
        replay = self.coordinator.propose(FAILURE, "replay")
        self.assertEqual(replay["source"], "recipe")
        self.assertEqual(self.llm.calls, 1)
        self.assertTrue(self.coordinator.record(FAILURE, replay, {"action_succeeded": True, "postcondition_passed": True})["continue"])

    def test_false_positive_and_degradation(self):
        proposal = self.coordinator.propose(FAILURE, "recover")
        self.assertFalse(self.coordinator.record(FAILURE, proposal, {"action_succeeded": True, "postcondition_passed": False})["continue"])
        self.assertEqual(self.store.load()["recipes"], [])
        self.assertEqual(self.coordinator.metrics()["false_recoveries"], 1)
        self.coordinator.record(FAILURE, proposal, {"action_succeeded": True, "postcondition_passed": True})
        rid = self.store.load()["recipes"][0]["id"]
        self.coordinator.promote(rid)
        replay = self.coordinator.propose(FAILURE, "replay")
        for _ in range(2):
            self.coordinator.record(FAILURE, replay, {"action_succeeded": False, "postcondition_passed": False})
        self.assertEqual(self.store.load()["recipes"][0]["state"], "degraded")

    def test_malformed_memory_is_preserved(self):
        path = Path(__file__).with_name("malformed_recipe_fixture.json")
        store = RecipeStore(path)
        with self.assertRaises(json.JSONDecodeError):
            Coordinator(store).propose(FAILURE, "replay")
        self.assertEqual(path.read_text(encoding="utf-8"), "{broken\n")

    def test_concurrent_updates(self):
        threads = [threading.Thread(target=lambda: self.coordinator.record(
            FAILURE, {"attempted": True, "source": "discovery", "plan": PLAN},
            {"action_succeeded": True, "postcondition_passed": True})) for _ in range(12)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(len(self.store.load()["recipes"]), 1)
        self.assertEqual(self.store.load()["recipes"][0]["successes"], 12)

    def test_disabled_disconnected_and_platform_isolation(self):
        self.assertFalse(self.coordinator.propose(FAILURE, "disabled")["attempted"])
        self.assertFalse(self.coordinator.propose({**FAILURE, "category": "disconnected"}, "recover")["attempted"])
        self.assertFalse(self.coordinator.propose({**FAILURE, "platform": "windows_chrome"}, "replay")["attempted"])

    def test_model_cannot_invent_selector(self):
        with self.assertRaises(ValueError):
            self.coordinator.propose({**FAILURE, "evidence": []}, "recover")

    def test_disconnection_is_not_a_ui_change(self):
        self.assertEqual(classify_exception(ConnectionError("device offline")), "disconnected")

    def test_android_adapter_does_not_repeat_satisfied_action(self):
        class Target:
            count = 1
            info = {"enabled": True}
            def click(self): raise AssertionError("click repeated")
        class Device:
            def __call__(self, **kwargs): return Target()
        result = AndroidAdapter(Device()).execute(PLAN, lambda: True)
        self.assertTrue(result["postcondition_passed"])

    def test_action_attempt_limit_is_one(self):
        clicks = []
        class Target:
            count = 1
            info = {"enabled": True}
            def click(self): clicks.append(1)
        class Device:
            def __call__(self, **kwargs): return Target()
        with patch.object(test_hook, "wait_for_postcondition", return_value=False):
            result = AndroidAdapter(Device()).execute(PLAN, lambda: False)
        self.assertEqual(len(clicks), 1)
        self.assertFalse(result["postcondition_passed"])

    def test_ollama_timeout_fails_closed(self):
        client = OllamaClient("http://localhost:11434", "configured-model", timeout=0.1)
        with patch.object(service.request, "build_opener") as builder:
            builder.return_value.open.side_effect = TimeoutError
            with self.assertRaises(TimeoutError):
                client.propose(FAILURE)

    def test_lanforge_monitor_discovers_all_and_deduplicates_errors(self):
        class Query:
            def get_as_json(self, url, **kwargs):
                return {
                    "/resource/all": {"resources": [{"1.2": {"hostname": "phone-host", "ctrl-ip": "192.168.1.2"}},
                                                   {"1.3": {"hostname": "tablet-host"}}]},
                    "/adb/": {"devices": [{"1.2.ABC": {"device": "phone", "password": "secret"}},
                                           {"1.3.DEF": {"device": "tablet"}}]},
                    "/ports/all/": {"interfaces": [{"1.4.eth0": {"status": "UP"}}]},
                    "/generic/": {"endpoints": [{"yt0": {"status": "Running", "last results": "ERROR selector failed"}}]},
                    "/events/last/50": {"events": []},
                    "/alerts/last/50": {"alerts": []},
                }[url]
        monitor = LanforgeMonitor("http://example.invalid:8080", "learned_receipe.json", query=Query())
        first = monitor.poll_once()
        second = monitor.poll_once()
        self.assertEqual(len(first["inventory"]["resources"]), 2)
        self.assertEqual(first["inventory"]["resources"][0]["hostname"], "phone-host")
        self.assertEqual(len(first["inventory"]["adb"]), 2)
        self.assertEqual(len(first["inventory"]["ports"]), 1)
        self.assertEqual(len(second["incidents"]), 1)
        self.assertNotIn("password", json.dumps(second))

    def test_manager_registration_accepts_private_ip_only(self):
        from .service import manager_url
        self.assertEqual(manager_url("192.168.200.1", 8080), "http://192.168.200.1:8080")
        for ip in ("127.0.0.1", "8.8.8.8", "localhost", "http://192.168.1.1"):
            with self.assertRaises(ValueError):
                manager_url(ip, 8080)

    def test_resource_discovery_survives_optional_api_error(self):
        class Query:
            def get_as_json(self, url, **kwargs):
                if url == "/resource/all":
                    return {"resources": [{"1.2": {"hostname": "client"}}]}
                raise ConnectionError("optional API unavailable")
        monitor = LanforgeMonitor("http://example.invalid:8080", "learned_receipe.json", query=Query())
        self.assertEqual(monitor.poll_once()["inventory"]["resources"][0]["hostname"], "client")


if __name__ == "__main__":
    unittest.main()
