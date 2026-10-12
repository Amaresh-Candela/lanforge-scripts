"""Validate central-only deployment settings before starting the API."""
import json
import sys
from pathlib import Path
from urllib import request

def check():
    store_parent = Path(__file__).resolve().parents[1]
    if not store_parent.is_dir():
        raise ValueError("RECOVERY_STORE parent directory does not exist")
    base_url = "http://192.168.200.182:11434"
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("RECOVERY_OLLAMA_BASE_URL must be an HTTP(S) URL")
    opener = request.build_opener(request.ProxyHandler({}))
    with opener.open(base_url + "/api/tags", timeout=5) as response:
        models = json.load(response).get("models", [])
    if "qwen3.8:latest" not in {item.get("name") for item in models}:
        raise ValueError("configured Ollama model is not listed at the base URL")
    return "Ollama model reachable; coordinator is ready to start"


if __name__ == "__main__":
    try:
        print(check())
    except Exception as exc:
        print("Recovery preflight failed: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
