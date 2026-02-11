import time
import requests
import subprocess
import os
import signal
import sys

PORT = 5005
BASE_URL = f"http://localhost:{PORT}"

def run_verification():
    print("Starting verification...")
    
    # helper for cleanup
    server_process = None
    
    try:
        # Start server
        env = os.environ.copy()
        env["PORT"] = str(PORT)
        # We need to make sure we are in the root directory
        cwd = "/Users/chrisbernardo/Desktop/ClawBrain"
        
        server_process = subprocess.Popen(
            [sys.executable, "llm_brain_api.py"],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        print("Waiting for server to start...")
        for i in range(10):
            try:
                requests.get(f"{BASE_URL}/health", timeout=1)
                print("Server is up!")
                break
            except:
                time.sleep(1)
        else:
            print("Server failed to start.")
            out, err = server_process.communicate()
            print("STDOUT:", out.decode())
            print("STDERR:", err.decode())
            return False

        # Send a dummy chat request
        print("Sending chat request...")
        payload = {"message": "Hello Verification Bot", "sender": "verifier"}
        # Note: This might cost money if using real API keys, but with mock or fail it should still log.
        # If no keys, it will fail and log error. Which is fine for testing traffic logger.
        
        try:
            resp = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
            print(f"Chat response: {resp.status_code}")
            # We don't care if it fails execution, just that it returns something.
        except Exception as e:
            print(f"Chat request failed (expected if no keys): {e}")

        # Check traffic
        print("Checking traffic log...")
        resp = requests.get(f"{BASE_URL}/api/traffic")
        if resp.status_code != 200:
            print(f"Failed to get traffic logs: {resp.status_code}")
            return False
            
        logs = resp.json().get("logs", [])
        if not logs:
            print("No traffic logs found!")
            return False
            
        # Verify the specific log
        found = False
        for log in logs:
            if "Verification Bot" in (log.get("prompt") or ""):
                found = True
                print(f"Found log entry: {log}")
                break
        
        if not found:
            print("Traffic log entry for 'Verification Bot' not found.")
            return False

        print("Verification Successful!")
        return True

    finally:
        if server_process:
            print("Stopping server...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
