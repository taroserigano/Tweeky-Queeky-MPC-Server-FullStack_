"""E2E test: chatbot recommendation returns real catalog items."""
import os
import sys
import time
import requests
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PORT = 5055
BASE_URL = f"http://localhost:{PORT}"


def wait_for_backend(timeout=25):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{BASE_URL}/api/products", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def run():
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    log_path = os.path.join(PROJECT_ROOT, "e2e_chatbot_server.log")
    log_file = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(PORT)],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=log_file,
        stderr=log_file,
    )
    try:
        if not wait_for_backend():
            raise RuntimeError(f"Backend did not start in time. See {log_path}")

        payload = {"query": "Recommend gaming gear"}
        res = requests.post(f"{BASE_URL}/api/agent/v2/chat", json=payload, timeout=20)
        res.raise_for_status()
        data = res.json()
        response = data.get("response", "")

        # Expected real catalog items from seed data
        expected = ["Secretlab Titan Evo 2022", "PlayStation 5", "Xbox Series X", "Razer BlackWidow V4"]
        if not any(name in response for name in expected):
            raise AssertionError("Response did not include expected catalog items")

        print("=== E2E RESPONSE START ===")
        print(response)
        print("=== E2E RESPONSE END ===")
        print("E2E PASS")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    run()
