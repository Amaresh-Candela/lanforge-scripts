# YouTube UI recovery

## Existing workflow and integration

`youtube/lf_interop_youtube.py` starts LANforge generic endpoints and receives the existing Android and Windows test logs. Android uses ADB and `uiautomator2` in `youtube_android_test.py`; Windows Chrome uses Selenium in the separate `real_application_test/youtube/youtube.py`. LANforge still owns traffic, measurements, reports, and test selection. The recovery hook is currently attached to the YouTube Stats for nerds action on each platform. Other LANforge and test-log errors are visible to the coordinator but are not automatically repaired without a live UI hook and a postcondition.

## Start on the AI computer

Copy the `lanforge-scripts` checkout to `192.168.200.182`, preserving `lanforge_client` and `py-scripts/real_application_tests`. Ensure Python is available (`.venv/Scripts/python.exe` or `python` on PATH) and Ollama has `qwen3.8:latest` loaded at `http://192.168.200.182:11434`. Run:

```bat
cd /d C:\path\to\lanforge-scripts\py-scripts\real_application_tests
start.bat
```

`start.bat` checks Ollama and runs only the coordinator on `http://192.168.200.182:8765`. It does not start a YouTube test. The coordinator stores recipes at `real_application_tests/learned_receipe.json` and writes bounded logs in that directory. Stop with Ctrl+C.

The addresses and model are written in `recovery/service.py`, `recovery/preflight.py`, `recovery/test_hook.py`, and the Windows `youtube/recovery_client.py`. There is no `.env` dependency. If the AI computer address changes, update those constants together.

## Run a test

Deploy the `recovery` directory beside `youtube` on the LANforge test machine and deploy the updated `youtube.py` plus `recovery_client.py` together on the Windows worker. Run the existing LANforge YouTube command with its normal arguments, including `--mgr MANAGER_IP --mgr_port 8080`. For example, substitute your actual manager, video, and upstream port:

```bat
python lf_interop_youtube.py --mgr MANAGER_IP --mgr_port 8080 --url VIDEO_URL --duration 1 --upstream_port UPSTREAM_PORT
```

The orchestrator sends that manager address to the coordinator. The coordinator polls LANforge through `lanforgeapi`: `/resource/all` supplies all manager resources, while `/adb/`, `/ports/all/`, `/generic/`, `/events/last/50`, and `/alerts/last/50` provide additional status and errors. Optional API failures are logged and retried on later polls. Existing uploaded test logs still go into the normal report and send a redacted 8 KB tail to `recovery_test_logs.jsonl`.

On a hooked UI failure, the local test sends bounded UI evidence to the AI computer. The coordinator first tries a validated recipe. Otherwise Ollama may propose a selector already present in that evidence. The local Selenium or `uiautomator2` hook requires one enabled target, clicks at most once, checks the original postcondition, and reports the result. Successful new plans are candidates; reviewed candidates can be promoted only while the coordinator is stopped:

```bat
python -m recovery.service promote RECIPE_ID
```

The coordinator runs on the AI computer. No model or agent service runs on LANforge or client devices. The test machines must be able to reach port 8765 on the AI computer, and the AI computer must be able to reach the LANforge manager's port 8080. These paths have not been verified in this workspace. This direct HTTP setup has no request authentication or transport encryption; keep port 8765 restricted to the dedicated test network through the host firewall.

## Verification and rollback

Mocked tests: `python -m unittest recovery.test_recovery -v` from `real_application_tests`; Windows hook tests: `python -m unittest discover -s youtube -p test_recovery_client.py -v` from `real_application_test`. Real Android and Chrome recovery and the AI-to-manager connection still require deployment testing.

To stop recovery immediately, stop `start.bat`; the hooks report an unavailable coordinator and preserve their original failure paths. To roll back the code, revert the Android and orchestrator hooks, remove the `recovery` directory, and revert the Windows YouTube hook and `recovery_client.py`. LANforge traffic and report calculations were not changed.
